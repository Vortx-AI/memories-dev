"""Specialized API connectors for glacier storage."""

# Import the DataSource base class first
from .base import DataSource

# Then import the connectors
from .osm import OSMConnector
from .overture import OvertureConnector
from .sentinel import SentinelConnector
from .landsat import LandsatConnector
from .planetary import PlanetaryConnector

__all__ = [
    'DataSource',  # Add DataSource to the exports
    'OSMConnector',
    'OvertureConnector',
    'SentinelConnector',
    'LandsatConnector',
    'PlanetaryConnector'
]

"""Initialize artifacts package."""

# Import connectors on demand to avoid circular imports 