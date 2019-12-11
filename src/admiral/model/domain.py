"""Mongo document models for Domains."""
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    BooleanField,
    DateTimeField,
    EmbeddedDocumentField,
    StringField,
)


class Agency(EmbeddedDocument):
    """Embedded document in a domain representing the owning agency."""

    id = StringField()
    name = StringField()


class Domain(Document):
    """Domain mongo document model."""

    domain = StringField(primary_key=True)
    agency = EmbeddedDocumentField(Agency)
    cyhy_stakeholder = BooleanField()
    scan_date = DateTimeField()

    meta = {"collection": "domains"}
