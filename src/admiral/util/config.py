"""Configuration utility functions."""

import yaml
from mongoengine import connect


def load_config(filename="/run/secrets/config.yml"):
    """Load a configuration file."""
    print(f"Reading configuration from {filename}")
    with open(filename, "r") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    return config


def connect_from_config(config=None):
    """Create connections from a confguration."""
    if not config:
        config = load_config()
    connections = config["connections"]
    for alias in connections.keys():
        connect(host=connections[alias]["uri"], alias=alias)
