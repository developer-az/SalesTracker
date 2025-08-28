"""
Nike retailer scraper.
"""

import json
import logging
from typing import Tuple

from bs4 import BeautifulSoup

from .base import BaseRetailer

logger = logging.getLogger(__name__)


class NikeRetailer(BaseRetailer):
    """Nike product scraper."""

    def __init__(self, **kwargs):
        super().__init__(name="nike", **kwargs)

    def is_supported_url(self, url: str) -> bool:
        """Check if URL is a Nike product page."""
        return "nike.com" in url

    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Tuple[str, str, str]:
        """Extract product information from Nike page."""
        try:
            name = "Product name not found"
            price = "Price not found"
            image = ""

            # Try JSON-LD data first
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if isinstance(data, list):
                        data = data[0] if data else {}

                    name = data.get("name", name)

                    # Extract price from offers
                    price_data = data.get("offers", {})
                    if isinstance(price_data, list):
                        price_data = price_data[0] if price_data else {}

                    price_value = price_data.get("price")
                    currency = price_data.get("priceCurrency", "USD")

                    if price_value:
                        price = f"${price_value}{currency}"

                    # Extract image
                    image_data = data.get("image")
                    if isinstance(image_data, list) and image_data:
                        image = image_data[0]
                    elif isinstance(image_data, str):
                        image = image_data

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.debug(f"Error parsing Nike JSON-LD: {e}")

            # Fallback to HTML selectors
            if name == "Product name not found":
                name_selectors = [
                    "h1#pdp_product_title",
                    'h1[data-test="product-title"]',
                    "h1.pdp-product-title",
                    "h1",
                    '[data-test="product-title"]',
                ]

                for selector in name_selectors:
                    name_element = soup.select_one(selector)
                    if name_element and name_element.get_text(strip=True):
                        name = name_element.get_text(strip=True)
                        break

            if price == "Price not found":
                price_selectors = [
                    '[data-test="product-price"]',
                    ".product-price",
                    ".price-current",
                    '[class*="price"]',
                    ".notranslate",
                ]

                for selector in price_selectors:
                    price_elements = soup.select(selector)
                    for price_element in price_elements:
                        price_text = price_element.get_text(strip=True)
                        if price_text and ("$" in price_text or "USD" in price_text):
                            price = price_text
                            break
                    if price != "Price not found":
                        break

            if not image:
                # Try to find main product image
                image_element = soup.find("meta", property="og:image")
                if image_element:
                    image = image_element.get("content", "")
                else:
                    # Try other image selectors
                    img_selectors = [
                        'img[data-test="product-image"]',
                        ".product-image img",
                        'img[alt*="product"], img[alt*="Product"]',
                    ]

                    for selector in img_selectors:
                        img_element = soup.select_one(selector)
                        if img_element:
                            image = img_element.get("src", "") or img_element.get("data-src", "")
                            if image:
                                break

            return name, price, image

        except Exception as e:
            logger.error(f"Error extracting Nike product info: {e}")
            return "Product name not found", "Price not found", ""
