"""Albatross — a calm arcade game about gliding from a mountain."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("albatross")
except PackageNotFoundError:  # pragma: no cover - only when running from source
    __version__ = "0.5.0"

__all__ = ["__version__"]
