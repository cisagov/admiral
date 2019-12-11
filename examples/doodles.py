#!/usr/bin/env python3
"""Sandbox."""

from mongoengine import context_managers

from admiral.model import Cert, Domain  # noqa: F401
from admiral.util import connect_from_config


def main():
    """Start of program."""
    connect_from_config()
    # with context_managers.switch_connection(Cert, "production"):
    import IPython

    IPython.embed()  # noqa: E702 <<< BREAKPOINT >>>


if __name__ == "__main__":
    main()
