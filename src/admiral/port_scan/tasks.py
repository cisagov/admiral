"""Port scanning Celery tasks."""

# Standard Python Libraries
import ipaddress
import subprocess  # nosec security considerations considered
import sys

# Third-Party Libraries
from celery import shared_task
from celery.utils.log import get_task_logger
from defusedxml.ElementTree import fromstring
from xmljson import badgerfish as bf

logger = get_task_logger(__name__)

QUICK_PORTS = [
    443,
    80,
    1720,
    22,
    49152,
    21,
    53,
    61001,
    3479,
    25,
    62078,
    3389,
    8080,
    8008,
    8081,
    9100,
    8010,
    4000,
    1248,
    248,
    175,
    8087,
    9010,
    9004,
    8111,
    4502,
    10800,
    7776,
    2770,
    9886,
]


def run_it(command):
    """External command execution helper.

    Returns the completed process.
    """
    logger.info(f"Executing command: {command}")

    try:
        if sys.version_info >= (3, 7):
            # TODO: Cannot use capture_output until we are using python 3.7
            # (which currently breaks celery)
            # Allowing shell execution via popen below.
            completed_process = subprocess.run(
                command, capture_output=True, shell=True, check=True  # nosec
            )
        else:
            # python 3.6 version
            completed_process = subprocess.run(
                command,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=True,  # nosec
                check=True,
            )
    except subprocess.CalledProcessError as err:
        # TODO: Log stderr since it is empty when reconstituted on the far side
        # Perhaps this will work in python 3.7
        logger.error(err.stderr.decode())
        raise err

    return completed_process


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def up_scan(ip):
    """Run a quick scan to determin if IP is up.

    Returns nmap output in JSON format.
    """
    # validate input
    valid_ip = ipaddress.ip_address(ip)
    # nnap requires a `-6` option if the target is IPv6
    # TODO: ICMP Timestamp and Address Mask pings are only valid for IPv4.
    v6_flag = "-6 " if valid_ip.version == 6 else ""
    ports = ",".join(str(i) for i in QUICK_PORTS)
    nmap_command = (
        f"sudo nmap {v6_flag}{valid_ip} --stats-every 60 -oX - "
        f"-n -sn -T4 --host-timeout 15m -PE -PP -PS{ports}"
    )
    completed_process = run_it(nmap_command)
    xml_string = completed_process.stdout.decode()
    data = bf.data(fromstring(xml_string))
    return data


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def port_scan(ip):
    """Run a scan to determine what services are responding.

    Returns nmap output in JSON format.
    """
    # validate input
    valid_ip = ipaddress.ip_address(ip)
    # nnap requires a `-6` option if the target is IPv6
    v6_flag = "-6 " if valid_ip.version == 6 else ""
    nmap_command = (
        f"sudo nmap {v6_flag}{valid_ip} --stats-every 60 -oX - "
        "-R -Pn -T4 --host-timeout 120m --max-scan-delay 5ms "
        "--max-retries 2 --min-parallelism 32 "
        "--defeat-rst-ratelimit -sV -O -sS -p1-65535"
    )
    completed_process = run_it(nmap_command)
    xml_string = completed_process.stdout.decode()
    data = bf.data(fromstring(xml_string))
    return data
