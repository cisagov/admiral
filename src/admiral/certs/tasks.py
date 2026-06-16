"""Certificate Transparency Log Celery tasks."""

# Standard Python Libraries
import json
import re

# Third-Party Libraries
from celery import shared_task
from celery.utils.log import get_task_logger
import requests

# We use the version number to identify our user-agent string
from .._version import __version__

logger = get_task_logger(__name__)

# A single domain label as accepted by this project: 2 to 63 lowercase
# alphanumeric characters with hyphens permitted in between.  This is stricter
# than RFC 1035 (which allows 1-char labels and is case-insensitive) because the
# original regex enforced the same constraints and the CT-log queries only need
# lowercase FQDNs.  Validating one label at a time avoids the catastrophic
# backtracking the previous combined regex was flagged for (flake8 DUO138 /
# ReDoS); see #106.
LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$")


def is_valid_domain_name(domain):
    """Return True if *domain* passes this project's domain-name rules.

    Rules: two or more labels, each 2-63 lowercase alphanumeric characters
    (hyphens allowed in the middle), with an optional trailing dot (FQDN form).
    These constraints are intentionally stricter than RFC 1035 because they
    mirror the original regex and match the CT-log query requirements.
    """
    if not isinstance(domain, str):
        return False
    if domain.endswith("."):
        domain = domain[:-1]
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    return all(LABEL_RE.match(label) for label in labels)


# Default timeout values for tasks that perform web requests. See
# "Warning' at https://docs.celeryq.dev/en/stable/userguide/tasks.html
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 30.0


@shared_task(
    autoretry_for=(Exception, requests.HTTPError, requests.exceptions.HTTPError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 16},
)
def summary_by_domain(domain, subdomains=True):
    """Fetch a summary of the certificates in the log.

    Arguments:
    domain -- the domain to query
    subdomains -- include certificates of subdomains

    """
    # validate input
    if not is_valid_domain_name(domain):
        raise ValueError(f"invalid domain name format: {domain}")

    # read SSLMate API key
    key = ""
    with open("/run/secrets/sslmate-api-key.txt") as file:
        key = file.read().rstrip()

    logger.info(f"Fetching certs from CT log for: {domain}")
    url = (
        f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains={subdomains}"
        f"&expand=dns_names&expand=cert_der"
    )
    req = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": f"admiral/{__version__}",
        },
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    )

    if req.ok:
        data = json.loads(req.content)
        return data
    else:
        req.raise_for_status()


@shared_task
def cert_by_issuance(issuance):
    """Fetch a certificate object from the issuance object.

    Arguments:
    issuance -- the certificate issuance record found in one or more logs

    """
    id = issuance["id"]
    logger.info(f"Fetching cert data from CT log for id: {id}.")

    return issuance["cert_der"]
