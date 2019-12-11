#!/usr/bin/env python3
"""load-certs: A tool to download certificates from CT logs.

This tool will download CT Logs via celery tasks and store them in a mongo
database.

Usage:
  load-certs [options] [--skipto=<domain>]
  load-certs (-h | --help)
  load-certs --version

Options:
  -s --skipto=<domain>     Skip to domain and continue
  -v --verbose             Print more detailed output
"""

import pprint
import time

from admiral.celery import configure_app
from admiral.certs.tasks import summary_by_domain, cert_by_id
from celery import group
import dateutil.parser as parser
from mongoengine import context_managers
from tqdm import tqdm

from admiral.model import Cert, Domain
from admiral.util import connect_from_config

# Globals
PP = pprint.PrettyPrinter(indent=4)
EARLIEST_EXPIRED_DATE = parser.parse("2018-10-01")


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


def get_new_log_ids(domain, max_expired_date, verbose=False):
    """Generate a sequence of new CT Log IDs.

    Arguments:
    domain -- the domain name to query
    max_expired_date -- a date to filter out expired certificates

    Yields a sequence of new, unique, log IDs.
    """
    if verbose:
        tqdm.write(f"requesting certificate list for: {domain}")
    expired = domain != "nasa.gov"  # NASA is breaking the CT Log
    cert_list = summary_by_domain.delay(domain, subdomains=True, expired=expired)
    cert_list = cert_list.get()
    duplicate_log_ids = set()
    for i in tqdm(cert_list, desc="Subjects", unit="entries", leave=False):
        log_id = i["min_cert_id"]
        cert_expiration_date = parser.parse(i["not_after"])
        if verbose:
            tqdm.write(
                f"id: {log_id}:\tex: {cert_expiration_date}\t"
                f'{i["name_value"]}...\t',
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
            yield (log_id)


def group_update_domain(domain, max_expired_date, verbose=False):
    """Create parallel tasks to download all new certificates with date filter.

    Arguments:
    domain -- domain name to query
    max_expired_date -- a date to filter out expired certificates

    Returns the number of certificates imported.
    """
    # create a list of signatures to be executed in parallel
    signatures = []
    for log_id in get_new_log_ids(domain.domain, max_expired_date, verbose):
        signatures.append(cert_by_id.s(log_id))

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
    for task, pem in tasks_to_results:
        cert, is_precert = Cert.from_pem(pem)
        cert.log_id = task.get("args")[0]  # get log_id from task
        if is_precert:
            # if this is a precert, we save to the precert collection
            with context_managers.switch_collection(Cert, "precerts"):
                cert.save()
        else:
            # this is not a precert, save to the cert collection
            cert.save()
    return len(job.tasks)


def load_certs(domains, skip_to=None, verbose=False):
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
            new_count = group_update_domain(domain, EARLIEST_EXPIRED_DATE, verbose)
            total_new_count += new_count
            if verbose or new_count > 0:
                tqdm.write(
                    f"{new_count} certificates were imported for " f"{domain.domain}"
                )
    return total_new_count


def main():
    """Start of program."""
    from docopt import docopt

    args = docopt(__doc__, version="v0.0.2")

    # create database connection
    connect_from_config()

    # configure celery
    configure_app()

    total_new_count = 0

    domains = Domain.objects(domain__ne="nasa.gov").batch_size(1)
    print(f"{domains.count()} domains to process")
    total_new_count += load_certs(domains, args["--skipto"], args["--verbose"])
    print(
        f"{total_new_count} certificates were imported for "
        f"{len(domains)} domains. (so far)"
    )

    domains = Domain.objects(domain="nasa.gov").batch_size(1)
    print("processing nasa (troublesome)")
    total_new_count += load_certs(domains, args["--skipto"], args["--verbose"])

    print(
        f"{total_new_count} certificates were imported for " f"{len(domains)} domains."
    )


if __name__ == "__main__":
    main()
