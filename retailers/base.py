"""
Base class for retailer scrapers.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseRetailer(ABC):
    """Abstract base class for retailer scrapers."""
    
    def __init__(self, name: str, user_agent: str = None, timeout: int = 10, retry_attempts: int = 3):
        self.name = name
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
    
    @abstractmethod
    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Tuple[str, str, str]:
        """Extract product name, price, and image URL from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object of the page
            url: Original product URL
            
        Returns:
            Tuple of (name, price, image_url)
        """
        pass
    
    @abstractmethod
    def is_supported_url(self, url: str) -> bool:
        """Check if the URL is supported by this retailer.
        
        Args:
            url: Product URL to check
            
        Returns:
            True if URL is supported, False otherwise
        """
        pass
    
    def scrape_product(self, url: str) -> Tuple[str, str, str]:
        """Scrape product information with retry logic and error handling.
        
        Args:
            url: Product URL to scrape
            
        Returns:
            Tuple of (name, price, image_url)
        """
        if not self.is_supported_url(url):
            logger.warning(f"URL not supported by {self.name}: {url}")
            return "Unsupported URL", "Price not found", ""
            
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                name, price, image = self.extract_product_info(soup, url)
                
                logger.info(f"Successfully scraped {self.name} product: {name} - {price}")
                return name, price, image
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"{self.name} scraping attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to scrape {self.name} product after {self.retry_attempts} attempts: {e}")
                    return "Product name not found", "Price not found", ""
                    
            except Exception as e:
                logger.error(f"Unexpected error scraping {self.name} product: {e}")
                return "Product name not found", "Price not found", ""
    
    def get_cache_key(self, url: str) -> str:
        """Generate cache key for a URL."""
        return f"{self.name}:{hash(url)}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get retailer metadata."""
        return {
            "name": self.name,
            "user_agent": self.user_agent,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts
        }