"""Tests for Certificate tasks."""

# Standard Python Libraries
import pprint

# Third-Party Libraries
# from cryptography import x509
# from cryptography.hazmat.backends import default_backend
import pytest

# from admiral.certs.tasks import cert_by_issuance, summary_by_domain

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
#         assert summary.get(timeout=60) is not None, "Summary result cannot be None"
#         assert len(summary.get()) > 0, "Summary should return at least one result"
#         PP.pprint(summary.get())
#         print(f"received {len(summary.get())} summary records")
#
#         # get the first id from the summaries
#         id = summary.get()[0]["id"]
#         print(f"requesting certificate for id: {id}")
#         first_cert = cert_by_issuance.delay(id)
#         pem = first_cert.get(timeout=60)
#         print("done")
#
#         cert = x509.load_pem_x509_certificate(bytes(pem, "utf-8"), default_backend())
#         print(f"certificate serial number: {cert.serial_number}")


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        ("example.com", True),
        ("sub.domain.example.gov", True),
        ("example.com.", True),  # a single trailing dot (FQDN form) is allowed
        ("a-b.c-d.com", True),  # hyphens are permitted inside labels
        ("cyber.dhs.gov", True),
        ("a..com", False),  # consecutive dots produce an empty label
        ("-bad.com", False),  # a label may not start with a hyphen
        ("bad-.com", False),  # a label may not end with a hyphen
        ("a", False),  # at least two labels are required
        ("", False),
        (None, False),  # non-string input should be rejected
        ("x.co", False),  # single-character labels are not accepted by this validator
        (("a" * 64) + ".com", False),  # a label may not exceed 63 characters
    ],
)
def test_is_valid_domain_name(domain, expected):
    """Accept domains that satisfy the project's validation rules."""
    # cisagov Libraries
    from admiral.certs.tasks import is_valid_domain_name

    assert is_valid_domain_name(domain) is expected
