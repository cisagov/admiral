#!/usr/bin/env pytest -vs

"""Tests for port scan tasks."""

# Standard Python Libraries
import pprint

# Third-Party Libraries
import pytest

# from admiral.port_scan.tasks import port_scan, up_scan

PP = pprint.PrettyPrinter(indent=4)


@pytest.fixture(scope="module")
def celery():
    """Celery app test fixture."""
    # cisagov Libraries
    from admiral.celery import celery

    return celery


@pytest.fixture(scope="module")
def host_ip():
    """Test fixture to resolve and return host_ip as a string."""
    # Third-Party Libraries
    import dns.resolver

    query = dns.resolver.query("scanme.nmap.org")
    assert len(query) > 0, "could not resolve target host name"
    return query[0].address


# These tests currently require the Docker Compose configuration to be running
# to function. This makes it difficult to perform standard Python testing.
# class TestPortScans:
#     """Test port scan celery tasks."""
#
#     def test_up_scan(self, celery, host_ip):
#         """Test up_scan task."""
#         ns1 = up_scan.delay(host_ip)
#         PP.pprint(ns1.get())
#
#     def test_port_scan(self, celery, host_ip):
#         """Test port_scan task."""
#         ns2 = port_scan.delay(host_ip)
#         PP.pprint(ns2.get())
