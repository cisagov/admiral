#!/usr/bin/env python3
"""load-certs: A tool to download certificates from CT logs.

This tool will download CT Logs via celery tasks and store them in a mongo
database.

Usage:
  load-certs [options] [--skipto=<domain>]
  load-certs (-h | --help)
  load-certs --version

Options:
  -d --dry-run             Do not modify database
  -s --skipto=<domain>     Skip to domain and continue
  -v --verbose             Print more detailed output
"""

# Standard Python Libraries
import base64
import pprint
import ssl
import time

# Third-Party Libraries
from celery import group
import dateutil.parser as parser
from dateutil.tz import UTC
from dateutil.utils import default_tzinfo
from docopt import docopt
from mongoengine import context_managers
from tqdm import tqdm

# cisagov Libraries
from admiral.celery import configure_app
from admiral.certs.tasks import cert_by_issuance, summary_by_domain
from admiral.model import Cert, Domain
from admiral.util import connect_from_config

# Globals
PP = pprint.PrettyPrinter(indent=4)
EARLIEST_EXPIRED_DATE = default_tzinfo(
    # Make the earliest expired date timezone aware. This date in 
    # particular represents the start of FY19, the fiscal year during
    # which Emergency Directive 19-01 went into effect. For more, see
    # https://www.cisa.gov/emergency-directive-19-01.
    parser.parse("2018-10-01"),
    UTC,
)


def cert_id_exists_in_database(log_id):
    """Check if a  ID already exists in the either certificate collection.

    Returns True if the id exists, False otherwise
    """
    c = Cert.objects(log_id=log_id)
    if c.count() > 0:
        return True
    with context_managers.switch_collection(Cert, "precerts"):
        c = Cert.objects(log_id=log_id)
        if c.count() > 0:
            return True
    return False


def get_new_log_issuances(domain, max_expired_date, verbose=False):
    """Generate a sequence of new CT Log issuances.

    Arguments:
    domain -- the domain name to query
    max_expired_date -- a date to filter out expired certificates

    Yields a sequence of new, unique, log issuances.

    """
    if verbose:
        tqdm.write(f"requesting certificate list for: {domain}")

    cert_list = summary_by_domain.delay(domain, subdomains=True)
    cert_list = cert_list.get()
    duplicate_log_ids = set()
    for i in tqdm(cert_list, desc="Subjects", unit="entries", leave=False):
        log_id = i["id"]
        name = i["dns_names"][0]  # take the first DNS name available
        cert_expiration_date = parser.parse(i["not_after"])
        if verbose:
            tqdm.write(
                f"id: {log_id}:\tex: {cert_expiration_date}\t" f"{name}...\t",
                end="",
            )
        if cert_expiration_date < max_expired_date:
            if verbose:
                tqdm.write("too old")
            continue
        # check to see if we have this certificate already
        if log_id in duplicate_log_ids or cert_id_exists_in_database(log_id):
            # we already have it, skip
            duplicate_log_ids.add(log_id)
            if verbose:
                tqdm.write("duplicate")
            continue
        else:
            duplicate_log_ids.add(log_id)
            if verbose:
                tqdm.write("will import")
            yield (i)


def group_update_domain(domain, max_expired_date, verbose=False, dry_run=False):
    """Create parallel tasks to download all new certificates with date filter.

    Arguments:
    domain -- domain name to query
    max_expired_date -- a date to filter out expired certificates

    Returns the number of certificates imported.

    """
    # create a list of signatures to be executed in parallel
    signatures = []

    for issuance in get_new_log_issuances(domain.domain, max_expired_date, verbose):
        signatures.append(cert_by_issuance.s(issuance))

    # create a job with all the signatures
    job = group(signatures)
    # send the group to the queue
    results = job.apply_async()

    # wait for the jobs to complete, updating our progress bar as we go
    with tqdm(total=len(signatures), desc="Certs", unit="certs", leave=False) as pbar:
        while not results.ready():
            pbar.update(results.completed_count() - pbar.n)
            time.sleep(0.5)

    # map the tasks to their corresponding results
    tasks_to_results = zip(job.tasks, results.join())

    # create x509 certificates from the results
    for task, result in tasks_to_results:
        data = base64.b64decode(result["data"])  # encoded in ASN.1 DER
        pem = ssl.DER_cert_to_PEM_cert(data)
        cert, is_precert = Cert.from_pem(pem)
        cert.log_id = task.get("args")[0]  # get log_id from task
        if is_precert:
            # if this is a precert, we save to the precert collection
            with context_managers.switch_collection(Cert, "precerts"):
                if not dry_run:
                    cert.save()
        else:
            # this is not a precert, save to the cert collection
            if not dry_run:
                cert.save()
    return len(job.tasks)


def load_certs(domains, skip_to=None, verbose=False, dry_run=False):
    """Load new certificates for the domain list."""
    total_new_count = 0
    with tqdm(domains, unit="domain") as pbar:
        for domain in pbar:
            pbar.set_description("%20s" % domain.domain)
            # skip to requested domain
            if skip_to is not None:
                if skip_to == domain.domain:
                    skip_to = None
                else:
                    continue
            # if domain.domain == "nasa.gov":
            #     continue
            if verbose:
                tqdm.write("-" * 80)
            new_count = group_update_domain(
                domain, EARLIEST_EXPIRED_DATE, verbose, dry_run
            )
            total_new_count += new_count
            if verbose or new_count > 0:
                tqdm.write(
                    f"{new_count} certificates were imported for " f"{domain.domain}"
                )
    return total_new_count


def main():
    """Start of program."""
    args = docopt(__doc__, version="v0.0.2")

    # create database connection
    connect_from_config()

    # configure celery
    configure_app()

    total_new_count = 0

    domains = Domain.objects(domain__ne="nasa.gov").batch_size(1)
    print(f"{domains.count()} domains to process")
    total_new_count += load_certs(
        domains, args["--skipto"], args["--verbose"], args["--dry-run"]
    )
    print(
        f"{total_new_count} certificates were imported for "
        f"{len(domains)} domains. (so far)"
    )

    domains = Domain.objects(domain="nasa.gov").batch_size(1)
    print("processing nasa (troublesome)")
    total_new_count += load_certs(
        domains, args["--skipto"], args["--verbose"], args["--dry-run"]
    )

    print(
        f"{total_new_count} certificates were imported for " f"{len(domains)} domains."
    )


if __name__ == "__main__":
    main()
