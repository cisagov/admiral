"""Utility functions."""
from .config import load_config, connect_from_config
from .domains import trim_domains

__all__ = ["trim_domains", "load_config", "connect_from_config"]
