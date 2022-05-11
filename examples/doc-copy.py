#!/usr/bin/env python3
"""Mongo document copier.

Be careful, this can easily give you a bad day.

Usage:
  doc-copy <from_connection> <to_connection>
  doc-copy --list-connections
  doc-copy (-h | --help)
  doc-copy --version

 Options:
    -l --list-connections   List the available connections.
"""
# Standard Python Libraries
import sys

# Third-Party Libraries
from docopt import docopt
from models import Domain
from mongoengine import context_managers
from tqdm import tqdm

# cisagov Libraries
from admiral.util import connect_from_config, load_config


def copy_all(model, from_alias, to_alias):
    """Copy all documents from one connection to another."""
    print(f"Querying all {model} from {from_alias}")
    with context_managers.switch_db(model, from_alias) as model:
        all = model.objects.all()
        print(f"Saving all {model} into {to_alias}")
        for x in tqdm(all, total=all.count(), desc="Copy", unit="docs"):
            with context_managers.switch_db(model, to_alias) as model:
                # MongoEngine tracks changes, we need to force the save
                # or we'll get nothing.
                x.save(force_insert=True)


def print_connections():
    """Display the available connection keys."""
    config = load_config()
    print("Connections in configuration: ")
    for i in list(config["connections"].keys()):
        print(f"\t{i}")


def main():
    """Start executing at main entry point."""
    args = docopt(__doc__, version="v0.0.1")

    if args["--list-connections"]:
        print_connections()
        sys.exit(0)

    from_alias = args["<from_connection>"]
    to_alias = args["<to_connection>"]

    # connect to databases
    connect_from_config()

    # # Copy all documents from certs collection
    # copy_all(Cert, from_alias, to_alias)
    #
    # # Copy all documents from precerts collection
    # with context_managers.switch_collection(Cert, "precerts"):
    #     copy_all(Cert, from_alias, to_alias)
    #

    copy_all(Domain, from_alias, to_alias)


if __name__ == "__main__":
    main()
