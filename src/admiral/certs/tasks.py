"""Certificate Transparency Log Celery tasks."""

# Standard Python Libraries
import json
import re

# Third-Party Libraries
from celery import shared_task
from celery.utils.log import get_task_logger
import requests

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
    rate_limit="10/h",
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

    # fetch api key
    key = ""
    with open("/run/secrets/sslmate-api-key.txt", "r") as file:
        key = file.read().rstrip()

    logger.info(f"Fetching certs from CT log for: {domain}")
    url = (
        f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains={subdomains}"
        f"&expand=dns_names&expand=cert"
    )
    req = requests.get(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "cyhy/2.0.0"},
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    )

    if req.ok:
        data = json.loads(req.content)
        return data
    else:
        req.raise_for_status()


@shared_task
def cert_by_id(issuance):
    """Fetch a certificate by log ID.

    Arguments:
    issuance -- the certificate record found in one or more logs

    """
    id = issuance["id"]
    logger.info(f"Fetching cert data from CT log for id: {id}.")

    return issuance["cert"]
