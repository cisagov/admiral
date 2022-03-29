"""Configuration utility functions."""

# Third-Party Libraries
from mongoengine import connect
import yaml


def load_config(filename="/run/secrets/config.yml"):
    """Load a configuration file."""
    print(f"Reading configuration from {filename}")
    with open(filename, "r") as stream:
        config = yaml.safe_load(stream)
    return config


def connect_from_config(config=None):
    """Create connections from a confguration."""
    if not config:
        config = load_config()
    connections = config["connections"]
    for alias in connections.keys():
        connect(host=connections[alias]["uri"], alias=alias)
