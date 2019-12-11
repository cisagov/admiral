"""Mongo document models for Certificate documents."""
from datetime import datetime

from mongoengine import Document
from mongoengine.fields import (
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
    StringField,
)
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from admiral.util import trim_domains


def get_sans_set(xcert):
    """Extract the set of subjects from the SAN extension.

    Arguments:
    xcert -- an x509 certificate object

    Returns a set of strings containing the subjects
    """
    try:
        san = xcert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        ).value
        dns_names = set(san.get_values_for_type(x509.DNSName))
    except x509.extensions.ExtensionNotFound:
        dns_names = set()
    # not all subjects have CNs: https://crt.sh/?id=1009394371
    for cn in xcert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME):
        # TODO make sure the cn is a correct type
        # what the hell is going on here: https://crt.sh/?id=174654356
        # ensure the cn is in the dns_names
        dns_names.add(cn.value)
    return dns_names


def get_earliest_sct(xcert):
    """Calculate the earliest time this certificate was logged to a CT log.

    If it was not logged by the CA, then the not_before time is returned.

    Arguments:
    xcert -- an x509 certificate object

    Returns (datetime, bool):
        datetime: the earliest calculated date.
        bool: True if an SCT was used, False otherwise
    """
    try:
        earliest = datetime.max
        scts = xcert.extensions.get_extension_for_class(
            x509.PrecertificateSignedCertificateTimestamps
        ).value
        for sct in scts:
            earliest = min(earliest, sct.timestamp)
        return earliest, True
    except x509.extensions.ExtensionNotFound:
        return xcert.not_valid_before, False


def is_poisioned(xcert):
    """Determine if an x509 certificate has a precertificate poision extension.

    Arguments:
    xcert -- an x509 certificate object

    Returns bool:
        True if an certificate was poisioned (pre-cert), False otherwise.
    """
    try:
        xcert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.PRECERT_POISON)
        return True
    except x509.extensions.ExtensionNotFound:
        return False


class Cert(Document):
    """Certificate mongo document model."""

    log_id = IntField(primary_key=True)
    # serial is 20 octets, see: https://tools.ietf.org/html/rfc5280#section-4.1.2.2
    serial = StringField(required=True)
    issuer = StringField(required=True)
    not_before = DateTimeField(required=True)
    not_after = DateTimeField(required=True)
    sct_or_not_before = DateTimeField(required=True)
    sct_exists = BooleanField(required=True)
    pem = StringField(required=True)
    _subjects = ListField(required=True, field=StringField(), db_field="subjects")
    _trimmed_subjects = ListField(
        required=True, field=StringField(), db_field="trimmed_subjects"
    )

    meta = {
        "collection": "certs",
        "indexes": [
            "+_subjects",
            "+_trimmed_subjects",
            {"fields": ("+issuer", "+serial"), "unique": True},
        ],
    }

    @property
    def subjects(self):
        """Getter for subjects."""
        return self._subjects

    @subjects.setter
    def subjects(self, values):
        """Subjects setter.

        Normalizes inputs, and dervices trimmed_subjects
        """
        self._subjects = list({i.lower() for i in values})
        self._trimmed_subjects = list(trim_domains(self._subjects))

    @property
    def trimmed_subjects(self):
        """Read-only property.  This is derived from the subjects."""
        return self._trimmed_subjects

    def to_x509(self):
        """Return an x509 subject for this certificate."""
        return x509.load_pem_x509_certificate(
            bytes(self.pem, "utf-8"), default_backend()
        )

    @classmethod
    def from_pem(cls, pem):
        """Create a Cert model object from a PEM certificate string.

        Arguments:
        pem -- PEM encoded certificate

        Returns (cert, precert):
            cert: a Cert model object
            precert: a boolean, True if this is a precertificate, False otherwise
        """
        xcert = x509.load_pem_x509_certificate(bytes(pem, "utf-8"), default_backend())
        dns_names = get_sans_set(xcert)

        sct_or_not_before, sct_exists = get_earliest_sct(xcert)

        cert = cls()
        cert.serial = hex(xcert.serial_number)[2:]
        cert.issuer = xcert.issuer.rfc4514_string()
        cert.not_before = xcert.not_valid_before
        cert.not_after = xcert.not_valid_after
        cert.sct_or_not_before = sct_or_not_before
        cert.sct_exists = sct_exists
        cert.pem = pem
        cert.subjects = dns_names
        return cert, is_poisioned(xcert)
