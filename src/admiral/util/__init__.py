"""Utility functions."""
from .config import connect_from_config, load_config
from .domains import trim_domains

__all__ = ["trim_domains", "load_config", "connect_from_config"]
