#!/usr/bin/env pytest -vs

"""Tests for Certificate tasks."""

# Standard Python Libraries
import pprint

# Third-Party Libraries
# from cryptography import x509
# from cryptography.hazmat.backends import default_backend
import pytest

# from admiral.certs.tasks import cert_by_id, summary_by_domain

PP = pprint.PrettyPrinter(indent=4)


@pytest.fixture(scope="module")
def celery():
    """Celery app test fixture."""
    # cisagov Libraries
    from admiral.celery import celery

    return celery


# This test currently requires the Docker Compose configuration to be running
# to function. This makes it difficult to perform standard Python testing.
# See https://github.com/cisagov/admiral/issues/9 for details.
# class TestCerts:
#     """Test certificate transparency tasks."""
#
#     # @pytest.mark.filterwarnings("ignore:'async' and 'await'")
#     def test_end_to_end(self, celery):
#         """Perform and end-to-end test of the certificate log tasks."""
#         summary = summary_by_domain.delay("cyber.dhs.gov")
#         assert summary.get(timeout=60) is not None, "Summary result should not be None"
#         assert len(summary.get()) > 0, "Summary should return at least one result"
#         PP.pprint(summary.get())
#         print(f"received {len(summary.get())} summary records")
#
#         # get the first id from the summaries
#         id = summary.get()[0]["id"]
#         print(f"requesting certificate for id: {id}")
#         first_cert = cert_by_id.delay(id)
#         pem = first_cert.get(timeout=60)
#         print("done")
#
#         cert = x509.load_pem_x509_certificate(bytes(pem, "utf-8"), default_backend())
#         print(f"certificate serial number: {cert.serial_number}")
