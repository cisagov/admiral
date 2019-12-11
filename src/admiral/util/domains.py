"""Utility functions."""


def trim_domains(domains):  # TODO make this more robust
    """Create a set of parent domain names from domain names.

    Arguments:
    domains -- a collection of domain strings

    Returns a set of trimmed domain names, converted to lowercase
    """
    trimmed = set()
    for domain in domains:
        domain = domain.lower()  # Ensure all domains are lowercase
        if domain.endswith(".fed.us"):
            trimmed.add(".".join(domain.split(".")[-3:]))
        else:
            trimmed.add(".".join(domain.split(".")[-2:]))
    return trimmed
