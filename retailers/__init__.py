"""
Retailers package for extensible retailer support.
"""

from .base import BaseRetailer
from .lululemon import LululemonRetailer
from .nike import NikeRetailer
from .registry import RetailerRegistry, registry

__all__ = ["BaseRetailer", "LululemonRetailer", "NikeRetailer", "RetailerRegistry", "registry"]
