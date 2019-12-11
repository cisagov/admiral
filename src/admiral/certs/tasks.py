"""Certificate Transparency Log Celery tasks."""

import requests
import json
import re

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# regexr.com/3e8n2
DOMAIN_NAME_RE = re.compile(
    r"^((?:([a-z0-9]\.|[a-z0-9][a-z0-9\-]{0,61}[a-z0-9])\.)+)"
    r"([a-z0-9]{2,63}|(?:[a-z0-9][a-z0-9\-]{0,61}[a-z0-9]))\.?$"
)


@shared_task(
    autoretry_for=(Exception, requests.HTTPError, requests.exceptions.HTTPError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 16},
)
def summary_by_domain(domain, subdomains=True, expired=False):
    """Fetch a summary of the certificates in the log.

    Arguments:
    domain -- the domain to query
    subdomains -- include certificates of subdomains
    expired -- include expired certificates
    """
    # validate input
    m = DOMAIN_NAME_RE.match(domain)
    if m is None:
        raise ValueError(f"invalid domain name format: {domain}")

    wildcard_param = "%." if subdomains else ""
    expired_param = "" if expired else "&exclude=expired"

    logger.info(f"Fetching certs from CT log for: {wildcard_param}{domain}")
    url = (
        f"https://crt.sh/?Identity={wildcard_param}{domain}{expired_param}"
        f"&output=json"
    )

    req = requests.get(url, headers={"User-Agent": "cyhy/2.0.0"})

    if req.ok:
        data = json.loads(req.content)
        if subdomains:
            # a query for the unwildcarded domain needs to be made separately
            data += summary_by_domain(domain, subdomains=False, expired=expired)
        return data
    else:
        req.raise_for_status()


@shared_task(
    autoretry_for=(Exception, requests.HTTPError, requests.exceptions.HTTPError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 16},
)
def cert_by_id(id):
    """Fetch a certificate by log ID."""
    logger.info(f"Fetching cert data from CT log for id: {id}.")

    url = f"https://crt.sh/?d={id}"
    req = requests.get(url, headers={"User-Agent": "cyhy/2.0.0"})

    if req.ok:
        return req.content.decode()
    else:
        req.raise_for_status()
