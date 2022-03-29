#!/usr/bin/env python3
"""Sandbox."""

# Third-Party Libraries
from mongoengine import context_managers

# cisagov Libraries
from admiral.model import Cert, Domain  # noqa: F401
from admiral.util import connect_from_config


def main():
    """Start of program."""
    print(f"Context manager loaded: {context_managers}")
    connect_from_config()
    # with context_managers.switch_connection(Cert, "production"):
    # Third-Party Libraries
    import IPython

    IPython.embed()  # noqa: E702 <<< BREAKPOINT >>>


if __name__ == "__main__":
    main()
