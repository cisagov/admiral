"""Test the functionality of the util sub-module."""

# Third-Party Libraries
from mongoengine import connect
from mongomock import MongoClient
import pytest

# cisagov Libraries
from admiral import util

VALID_CONFIG_FILE = "tests/data/valid_config.yml"


@pytest.fixture(scope="session")
def valid_config():
    """Load a sample configuration for reuse."""
    return util.load_config(VALID_CONFIG_FILE)


def test_load_config_valid():
    """Test that a valid configuration file loads."""
    loaded_config = util.load_config(VALID_CONFIG_FILE)
    assert (
        "connections" in loaded_config
    ), "Missing connections key in sample configuration"
    for section in ["local", "production"]:
        assert (
            section in loaded_config["connections"]
        ), f"Missing the {section} connection in the sample configuration"
        assert (
            loaded_config["connections"][section].get("uri") is not None
        ), f"The {section} connection is missing the uri key"


def test_connect_from_config_valid(valid_config):
    """Test that a valid configuration connects to appropriate connections."""
    connections = valid_config["connections"]
    for alias in connections.keys():
        connect(
            host=connections[alias]["uri"], mongo_client_class=MongoClient, alias=alias
        )
