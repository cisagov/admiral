#!/usr/bin/env pytest -vs
"""Tests for Cert documents."""

from datetime import datetime

import dateutil.tz as tz
import pytest
import mongoengine

from admiral.model import Cert

# curl https://crt.sh/?d=1034418093
CISA_PEM = """
-----BEGIN CERTIFICATE-----
MIIE3DCCBGKgAwIBAgIQAiz5F+UGMv/q76orp8LkVDAKBggqhkjOPQQDAjBMMQsw
CQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMSYwJAYDVQQDEx1EaWdp
Q2VydCBFQ0MgU2VjdXJlIFNlcnZlciBDQTAeFw0xODEyMTAwMDAwMDBaFw0xOTEy
MTAxMjAwMDBaMIGCMQswCQYDVQQGEwJVUzEdMBsGA1UECBMURGlzdHJpY3QgT2Yg
Q29sdW1iaWExEzARBgNVBAcTCldhc2hpbmd0b24xKDAmBgNVBAoTH0RlcGFydG1l
bnQgb2YgSG9tZWxhbmQgU2VjdXJpdHkxFTATBgNVBAMTDHd3dzIuZGhzLmdvdjBZ
MBMGByqGSM49AgEGCCqGSM49AwEHA0IABEf+LlTKhM1jbkNsLzi4tavqExkFdAAR
clUqsDWhMkfx+kEm4u3zfZlkH8vErU7N6m8M0Y1liLS5JkD7QIxexgGjggLtMIIC
6TAfBgNVHSMEGDAWgBSjneYf+do5T8Bu6JHLlaXaMeIKnzAdBgNVHQ4EFgQU0+4w
g42B5ulyrktu89vO+xzFaiwwLwYDVR0RBCgwJoIMd3d3Mi5kaHMuZ292gghjaXNh
LmdvdoIMd3d3LmNpc2EuZ292MA4GA1UdDwEB/wQEAwIHgDAdBgNVHSUEFjAUBggr
BgEFBQcDAQYIKwYBBQUHAwIwaQYDVR0fBGIwYDAuoCygKoYoaHR0cDovL2NybDMu
ZGlnaWNlcnQuY29tL3NzY2EtZWNjLWcxLmNybDAuoCygKoYoaHR0cDovL2NybDQu
ZGlnaWNlcnQuY29tL3NzY2EtZWNjLWcxLmNybDBMBgNVHSAERTBDMDcGCWCGSAGG
/WwBATAqMCgGCCsGAQUFBwIBFhxodHRwczovL3d3dy5kaWdpY2VydC5jb20vQ1BT
MAgGBmeBDAECAjB7BggrBgEFBQcBAQRvMG0wJAYIKwYBBQUHMAGGGGh0dHA6Ly9v
Y3NwLmRpZ2ljZXJ0LmNvbTBFBggrBgEFBQcwAoY5aHR0cDovL2NhY2VydHMuZGln
aWNlcnQuY29tL0RpZ2lDZXJ0RUNDU2VjdXJlU2VydmVyQ0EuY3J0MAkGA1UdEwQC
MAAwggEEBgorBgEEAdZ5AgQCBIH1BIHyAPAAdgDuS723dc5guuFCaR+r4Z5mow9+
X7By2IMAxHuJeqj9ywAAAWeZO6lyAAAEAwBHMEUCIARvGJh2Lt3EAia6g+pPHQ0n
codkc3uQfeoAf5klXxVDAiEA4aP5wfp6wz2G+/5XWzTh6ztrOsvEyms/a0Sk1lQz
MzYAdgCHdb/nWXz4jEOZX73zbv9WjUdWNv9KtWDBtOr/XqCDDwAAAWeZO6pOAAAE
AwBHMEUCIQC0I8Qh87KneltxpiSKahQJXm2Ikpd1/oav4aKOJdQGnQIgKv74UPtk
OKqbqrBW4uYFLP3y67P1dlhVesUNyxuQgwIwCgYIKoZIzj0EAwIDaAAwZQIxAPyq
Jb1n5AM1zhzisDrfz2WqcPGxYQaJI5i5sOSc3jru6WeqA6WwAo4d7lKwYm+H5gIw
d4pMM9+oGq5+HKzkP0tS2n2xbh5VOiYJnA0Bd7qHmCXvVA2QoGBMi6opNcQrc4ND
-----END CERTIFICATE-----
"""


@pytest.fixture(scope="class", autouse=True)
def connection():
    """Create connections for tests to use."""
    from mongoengine import connect

    connect(host="mongomock://localhost", alias="default")


class TestCerts:
    """Cert document tests."""

    def test_empty_creation(self):
        """Create a new cert, and save it."""
        cert = Cert()
        # lots of fields are required, so this should fail
        with pytest.raises(mongoengine.errors.ValidationError):
            cert.save()

    def test_subjects(self):
        """Validate that subjects and trimmed_subjects are calulcated correctly."""
        cert = Cert()
        cert.subjects = ["cisa.gov", "cyber.dhs.gov"]
        assert set(cert.trimmed_subjects) == {"cisa.gov", "dhs.gov"}

    def test_simple_creation(self):
        """Create a new user, and save it."""
        cert = Cert()
        cert.log_id = 654321
        cert.serial = "123456"
        cert.issuer = "CISA Super Secure CA"
        cert.not_before = datetime.now(tz.tzutc())
        cert.not_after = datetime.now(tz.tzutc())
        cert.sct_or_not_before = datetime.now(tz.tzutc())
        cert.sct_exists = True
        cert.pem = "Not a PEM"
        cert.subjects = ["cisa.gov"]
        cert.save()

    def test_from_pem(self):
        """Verify Cert creation from a PEM blob."""
        cert, is_poisioned = Cert.from_pem(CISA_PEM)
        assert is_poisioned is False
        cert.log_id = 123
        cert.save()
