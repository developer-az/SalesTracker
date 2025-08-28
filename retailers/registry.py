"""
Retailer registry and scraping coordination.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .base import BaseRetailer
from .lululemon import LululemonRetailer
from .nike import NikeRetailer

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self.cache = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[tuple]:
        """Get cached value if still valid."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: tuple, ttl: Optional[int] = None):
        """Set cached value with TTL."""
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)

    def clear(self):
        """Clear all cached values."""
        self.cache.clear()

    def size(self) -> int:
        """Get number of cached items."""
        return len(self.cache)


class RetailerRegistry:
    """Registry and coordinator for retailer scrapers."""

    def __init__(self, enable_cache: bool = True, cache_ttl: int = 3600):
        self.retailers: Dict[str, BaseRetailer] = {}
        self.enable_cache = enable_cache
        self.cache = SimpleCache(cache_ttl) if enable_cache else None
        self._register_default_retailers()

    def _register_default_retailers(self):
        """Register default retailers."""
        self.register_retailer(LululemonRetailer())
        self.register_retailer(NikeRetailer())

    def register_retailer(self, retailer: BaseRetailer):
        """Register a new retailer."""
        self.retailers[retailer.name] = retailer
        logger.info(f"Registered retailer: {retailer.name}")

    def get_retailer(self, name: str) -> Optional[BaseRetailer]:
        """Get retailer by name."""
        return self.retailers.get(name)

    def get_retailer_for_url(self, url: str) -> Optional[BaseRetailer]:
        """Find appropriate retailer for a URL."""
        for retailer in self.retailers.values():
            if retailer.is_supported_url(url):
                return retailer
        return None

    def scrape_product(self, url: str, use_cache: bool = True) -> Tuple[str, str, str]:
        """Scrape product using appropriate retailer."""
        retailer = self.get_retailer_for_url(url)

        if not retailer:
            logger.warning(f"No retailer found for URL: {url}")
            return "Unsupported retailer", "Price not found", ""

        # Check cache first
        if use_cache and self.cache:
            cache_key = retailer.get_cache_key(url)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached result for {url}")
                return cached_result

        # Scrape and cache result
        result = retailer.scrape_product(url)

        if use_cache and self.cache and result[0] != "Product name not found":
            cache_key = retailer.get_cache_key(url)
            self.cache.set(cache_key, result)
            logger.debug(f"Cached result for {url}")

        return result

    def scrape_multiple(self, urls: List[str], use_cache: bool = True, delay: float = 1.0) -> List[dict]:
        """Scrape multiple products with rate limiting."""
        results = []

        for i, url in enumerate(urls):
            if i > 0 and delay > 0:
                time.sleep(delay)  # Rate limiting

            try:
                name, price, image = self.scrape_product(url, use_cache=use_cache)
                retailer = self.get_retailer_for_url(url)

                results.append(
                    {
                        "url": url,
                        "name": name,
                        "price": price,
                        "image": image,
                        "retailer": retailer.name if retailer else "unknown",
                        "timestamp": datetime.now().isoformat(),
                        "success": name != "Product name not found",
                    }
                )
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                results.append(
                    {
                        "url": url,
                        "name": f"Error: {str(e)}",
                        "price": "N/A",
                        "image": "",
                        "retailer": "unknown",
                        "timestamp": datetime.now().isoformat(),
                        "success": False,
                    }
                )

        return results

    def get_supported_retailers(self) -> List[str]:
        """Get list of supported retailer names."""
        return list(self.retailers.keys())

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.cache:
            return {"enabled": False}

        return {"enabled": True, "size": self.cache.size(), "default_ttl": self.cache.default_ttl}

    def clear_cache(self):
        """Clear all cached results."""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")


# Global registry instance
registry = RetailerRegistry()
