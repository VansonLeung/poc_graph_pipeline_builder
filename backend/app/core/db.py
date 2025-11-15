"""Database helper utilities."""

from __future__ import annotations

from neo4j import Driver
from config import Config

_driver: Driver | None = None


def get_driver() -> Driver:
    """Return a shared Neo4j driver instance."""
    global _driver
    if _driver is None:
        _driver = Config.get_neo4j_driver()
    return _driver


def close_driver() -> None:
    """Close the shared Neo4j driver if it is open."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
