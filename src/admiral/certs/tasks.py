"""Certificate Transparency Log Celery tasks."""

# Standard Python Libraries
import json
import re

# Third-Party Libraries
from celery import shared_task
from celery.utils.log import get_task_logger
import requests
import yaml

# We use the version number to identify our user-agent string
from .._version import __version__

logger = get_task_logger(__name__)

# regexr.com/3e8n2
DOMAIN_NAME_RE = re.compile(
    r"^((?:([a-z0-9]\.|[a-z0-9][a-z0-9\-]{0,61}[a-z0-9])\.)+)"
    r"([a-z0-9]{2,63}|(?:[a-z0-9][a-z0-9\-]{0,61}[a-z0-9]))\.?$"
)

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
    m = DOMAIN_NAME_RE.match(domain)
    if m is None:
        raise ValueError(f"invalid domain name format: {domain}")

    # grab censys credentials
    with open("/run/secrets/censys.yml") as stream:
        creds = yaml.safe_load(stream)

    logger.info(f"Fetching certs from CT log for: {domain}")
    url = "https://search.censys.io/v2/certificates/search"
    query = f"names:{domain}" if subdomains else f"names={domain}"
    req = requests.get(
        url,
        auth=(creds["id"], creds["secret"]),
        params={"q": f"{query}"},
        headers={
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
