"""
Lululemon retailer scraper.
"""

import json
import logging
from typing import Tuple

from bs4 import BeautifulSoup

from .base import BaseRetailer

logger = logging.getLogger(__name__)


class LululemonRetailer(BaseRetailer):
    """Lululemon product scraper."""

    def __init__(self, **kwargs):
        super().__init__(name="lululemon", **kwargs)

    def is_supported_url(self, url: str) -> bool:
        """Check if URL is a Lululemon product page."""
        return "shop.lululemon.com" in url

    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Tuple[str, str, str]:
        """Extract product information from Lululemon page."""
        try:
            # Try to find JSON-LD data first (primary method)
            json_scripts = soup.find_all("script", type="application/ld+json")

            name = "Product name not found"
            price = "Price not found"
            image = ""

            # Parse JSON-LD data
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = data[0] if data else {}

                    if data.get("@type") == "Product":
                        name = data.get("name", name)

                        # Extract price from offers
                        offers = data.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}

                        price_value = offers.get("price")
                        currency = offers.get("priceCurrency", "USD")

                        if price_value:
                            price = f"${price_value}{currency}"

                        # Extract image
                        image_data = data.get("image", [])
                        if isinstance(image_data, list) and image_data:
                            image = image_data[0]
                        elif isinstance(image_data, str):
                            image = image_data

                        break

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.debug(f"Error parsing JSON-LD data: {e}")
                    continue

            # Fallback to HTML parsing if JSON-LD fails
            if name == "Product name not found":
                # Try various selectors for name
                name_selectors = [
                    'h1[data-testid="pdp-product-name"]',
                    "h1.pdp-product-name",
                    "h1",
                    '[data-testid="product-name"]',
                ]

                for selector in name_selectors:
                    name_element = soup.select_one(selector)
                    if name_element and name_element.get_text(strip=True):
                        name = name_element.get_text(strip=True)
                        break

            if price == "Price not found":
                # Try various selectors for price
                price_selectors = ['[data-testid="product-price"]', ".price", ".product-price", '[class*="price"]']

                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element and price_element.get_text(strip=True):
                        price = price_element.get_text(strip=True)
                        break

            if not image:
                # Try to find main product image
                image_selectors = [
                    'meta[property="og:image"]',
                    'img[data-testid="product-image"]',
                    ".product-image img",
                    'img[alt*="product"], img[alt*="Product"]',
                ]

                for selector in image_selectors:
                    if selector.startswith("meta"):
                        img_element = soup.select_one(selector)
                        if img_element:
                            image = img_element.get("content", "")
                    else:
                        img_element = soup.select_one(selector)
                        if img_element:
                            image = img_element.get("src", "") or img_element.get("data-src", "")

                    if image:
                        break

            return name, price, image

        except Exception as e:
            logger.error(f"Error extracting Lululemon product info: {e}")
            return "Product name not found", "Price not found", ""
