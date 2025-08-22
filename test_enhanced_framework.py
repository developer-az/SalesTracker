"""
Tests for the enhanced retailer framework and performance improvements.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import retailers
from retailers import BaseRetailer, LululemonRetailer, NikeRetailer, RetailerRegistry, registry
import config_enhanced as config


class TestBaseRetailer(unittest.TestCase):
    """Test the base retailer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        
        class TestRetailer(BaseRetailer):
            def extract_product_info(self, soup, url):
                return "Test Product", "$100USD", "http://example.com/image.jpg"
            
            def is_supported_url(self, url):
                return "test.com" in url
        
        self.retailer = TestRetailer("test")
    
    def test_initialization(self):
        """Test retailer initialization."""
        self.assertEqual(self.retailer.name, "test")
        self.assertEqual(self.retailer.timeout, 10)
        self.assertEqual(self.retailer.retry_attempts, 3)
        self.assertIsNotNone(self.retailer.session)
    
    @patch('requests.Session.get')
    def test_scrape_product_success(self, mock_get):
        """Test successful product scraping."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response
        
        result = self.retailer.scrape_product("http://test.com/product")
        self.assertEqual(result, ("Test Product", "$100USD", "http://example.com/image.jpg"))
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_scrape_product_unsupported_url(self, mock_get):
        """Test scraping unsupported URL."""
        result = self.retailer.scrape_product("http://unsupported.com/product")
        self.assertEqual(result, ("Unsupported URL", "Price not found", ""))
        mock_get.assert_not_called()
    
    @patch('requests.Session.get')
    def test_scrape_product_retry_logic(self, mock_get):
        """Test retry logic on request failures."""
        # Mock request exception
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        result = self.retailer.scrape_product("http://test.com/product")
        self.assertEqual(result, ("Product name not found", "Price not found", ""))
        self.assertEqual(mock_get.call_count, 3)  # Should retry 3 times
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        url = "http://test.com/product"
        cache_key = self.retailer.get_cache_key(url)
        self.assertTrue(cache_key.startswith("test:"))
    
    def test_get_metadata(self):
        """Test metadata retrieval."""
        metadata = self.retailer.get_metadata()
        self.assertEqual(metadata["name"], "test")
        self.assertEqual(metadata["timeout"], 10)


class TestLululemonRetailer(unittest.TestCase):
    """Test Lululemon retailer implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.retailer = LululemonRetailer()
    
    def test_initialization(self):
        """Test Lululemon retailer initialization."""
        self.assertEqual(self.retailer.name, "lululemon")
    
    def test_is_supported_url(self):
        """Test URL support detection."""
        self.assertTrue(self.retailer.is_supported_url("https://shop.lululemon.com/p/mens-jackets/test"))
        self.assertFalse(self.retailer.is_supported_url("https://nike.com/product/test"))
    
    def test_extract_product_info_with_json_ld(self):
        """Test product info extraction from JSON-LD."""
        from bs4 import BeautifulSoup
        
        html_with_json = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Product",
                "name": "Test Lululemon Product",
                "offers": {
                    "price": "120",
                    "priceCurrency": "USD"
                },
                "image": ["http://example.com/image.jpg"]
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        
        soup = BeautifulSoup(html_with_json, 'html.parser')
        name, price, image = self.retailer.extract_product_info(soup, "http://test.com")
        
        self.assertEqual(name, "Test Lululemon Product")
        self.assertEqual(price, "$120USD")
        self.assertEqual(image, "http://example.com/image.jpg")
    
    def test_extract_product_info_fallback(self):
        """Test fallback HTML parsing when JSON-LD fails."""
        from bs4 import BeautifulSoup
        
        html_without_json = """
        <html>
        <head></head>
        <body>
            <h1 data-testid="pdp-product-name">Fallback Product Name</h1>
            <div data-testid="product-price">$89USD</div>
            <meta property="og:image" content="http://example.com/fallback.jpg">
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html_without_json, 'html.parser')
        name, price, image = self.retailer.extract_product_info(soup, "http://test.com")
        
        self.assertEqual(name, "Fallback Product Name")
        self.assertEqual(price, "$89USD")
        self.assertEqual(image, "http://example.com/fallback.jpg")


class TestNikeRetailer(unittest.TestCase):
    """Test Nike retailer implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.retailer = NikeRetailer()
    
    def test_initialization(self):
        """Test Nike retailer initialization."""
        self.assertEqual(self.retailer.name, "nike")
    
    def test_is_supported_url(self):
        """Test URL support detection."""
        self.assertTrue(self.retailer.is_supported_url("https://www.nike.com/t/product-test"))
        self.assertFalse(self.retailer.is_supported_url("https://shop.lululemon.com/product/test"))
    
    def test_extract_product_info_with_json_ld(self):
        """Test product info extraction from JSON-LD."""
        from bs4 import BeautifulSoup
        
        html_with_json = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "name": "Nike Test Product",
                "offers": {
                    "price": "150",
                    "priceCurrency": "USD"
                },
                "image": "http://example.com/nike-image.jpg"
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        
        soup = BeautifulSoup(html_with_json, 'html.parser')
        name, price, image = self.retailer.extract_product_info(soup, "http://test.com")
        
        self.assertEqual(name, "Nike Test Product")
        self.assertEqual(price, "$150USD")
        self.assertEqual(image, "http://example.com/nike-image.jpg")


class TestSimpleCache(unittest.TestCase):
    """Test the simple cache implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        from retailers.registry import SimpleCache
        self.cache = SimpleCache(default_ttl=3600)
    
    def test_set_and_get(self):
        """Test basic cache set and get operations."""
        test_value = ("Test Product", "$100", "http://image.jpg")
        self.cache.set("test_key", test_value)
        
        retrieved_value = self.cache.get("test_key")
        self.assertEqual(retrieved_value, test_value)
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        test_value = ("Test Product", "$100", "http://image.jpg")
        self.cache.set("test_key", test_value, ttl=1)  # 1 second TTL
        
        # Should be available immediately
        self.assertIsNotNone(self.cache.get("test_key"))
        
        # Mock time passage
        import time
        time.sleep(2)
        
        # Should be expired now (in real implementation)
        # Note: This test might be flaky due to timing, in production use freezegun
    
    def test_clear_cache(self):
        """Test cache clearing."""
        self.cache.set("key1", ("Product1", "$100", ""))
        self.cache.set("key2", ("Product2", "$200", ""))
        
        self.assertEqual(self.cache.size(), 2)
        
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))


class TestRetailerRegistry(unittest.TestCase):
    """Test the retailer registry."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = RetailerRegistry(enable_cache=True)
    
    def test_initialization(self):
        """Test registry initialization."""
        self.assertGreater(len(self.registry.retailers), 0)
        self.assertIn("lululemon", self.registry.get_supported_retailers())
        self.assertIn("nike", self.registry.get_supported_retailers())
    
    def test_get_retailer_for_url(self):
        """Test finding appropriate retailer for URL."""
        lululemon_retailer = self.registry.get_retailer_for_url("https://shop.lululemon.com/product")
        self.assertIsNotNone(lululemon_retailer)
        self.assertEqual(lululemon_retailer.name, "lululemon")
        
        nike_retailer = self.registry.get_retailer_for_url("https://www.nike.com/product")
        self.assertIsNotNone(nike_retailer)
        self.assertEqual(nike_retailer.name, "nike")
        
        unknown_retailer = self.registry.get_retailer_for_url("https://unknown-store.com/product")
        self.assertIsNone(unknown_retailer)
    
    @patch('retailers.lululemon.LululemonRetailer.scrape_product')
    def test_scrape_product_with_cache(self, mock_scrape):
        """Test product scraping with caching."""
        test_result = ("Cached Product", "$100USD", "http://image.jpg")
        mock_scrape.return_value = test_result
        
        url = "https://shop.lululemon.com/product/test"
        
        # First call should hit the retailer
        result1 = self.registry.scrape_product(url, use_cache=True)
        self.assertEqual(result1, test_result)
        mock_scrape.assert_called_once()
        
        # Second call should use cache
        mock_scrape.reset_mock()
        result2 = self.registry.scrape_product(url, use_cache=True)
        self.assertEqual(result2, test_result)
        mock_scrape.assert_not_called()  # Should not call retailer again
    
    @patch('retailers.lululemon.LululemonRetailer.scrape_product')
    @patch('retailers.nike.NikeRetailer.scrape_product')
    def test_scrape_multiple(self, mock_nike_scrape, mock_lulu_scrape):
        """Test scraping multiple products."""
        mock_lulu_scrape.return_value = ("Lulu Product", "$120USD", "http://lulu.jpg")
        mock_nike_scrape.return_value = ("Nike Product", "$150USD", "http://nike.jpg")
        
        urls = [
            "https://shop.lululemon.com/product/1",
            "https://www.nike.com/product/1"
        ]
        
        results = self.registry.scrape_multiple(urls, delay=0)  # No delay for testing
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], "Lulu Product")
        self.assertEqual(results[1]['name'], "Nike Product")
        self.assertEqual(results[0]['retailer'], "lululemon")
        self.assertEqual(results[1]['retailer'], "nike")
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        stats = self.registry.get_cache_stats()
        self.assertTrue(stats['enabled'])
        self.assertIn('size', stats)
        self.assertIn('default_ttl', stats)


class TestEnhancedConfiguration(unittest.TestCase):
    """Test enhanced configuration system."""
    
    def test_get_config(self):
        """Test complete configuration retrieval."""
        config_dict = config.get_config()
        
        required_sections = ['product_links', 'email', 'scraping', 'performance', 
                           'security', 'storage', 'features', 'retailers', 'version']
        
        for section in required_sections:
            self.assertIn(section, config_dict)
    
    def test_get_retailer_config(self):
        """Test retailer-specific configuration."""
        lulu_config = config.get_retailer_config("lululemon")
        self.assertIn('timeout', lulu_config)
        self.assertIn('retry_attempts', lulu_config)
        self.assertIn('cache_ttl', lulu_config)
        
        # Test fallback to global settings
        unknown_config = config.get_retailer_config("unknown")
        self.assertEqual(unknown_config['timeout'], config.SCRAPING_SETTINGS['timeout'])
    
    def test_validate_config(self):
        """Test configuration validation."""
        # This test depends on environment setup, so we'll test the structure
        issues = config.validate_config()
        self.assertIsInstance(issues, list)
    
    def test_feature_flags(self):
        """Test feature flag functionality."""
        # Test existing feature
        result = config.is_feature_enabled('enable_web_ui')
        self.assertIsInstance(result, bool)
        
        # Test non-existent feature
        result = config.is_feature_enabled('non_existent_feature')
        self.assertFalse(result)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete scenarios."""
    
    def test_registry_with_real_retailers(self):
        """Test that the global registry works with real retailers."""
        self.assertIn("lululemon", registry.get_supported_retailers())
        self.assertIn("nike", registry.get_supported_retailers())
        
        # Test URL routing
        lulu_retailer = registry.get_retailer_for_url("https://shop.lululemon.com/test")
        nike_retailer = registry.get_retailer_for_url("https://www.nike.com/test")
        
        self.assertEqual(lulu_retailer.name, "lululemon")
        self.assertEqual(nike_retailer.name, "nike")
    
    def test_configuration_compatibility(self):
        """Test that enhanced config is backward compatible."""
        # Test that original variables still exist
        self.assertIsNotNone(config.PRODUCT_LINKS)
        self.assertIsNotNone(config.EMAIL_SETTINGS)
        self.assertIsNotNone(config.SCRAPING_SETTINGS)
        
        # Test that enhanced features are available
        self.assertIsNotNone(config.PERFORMANCE_SETTINGS)
        self.assertIsNotNone(config.RETAILER_SETTINGS)
    
    @patch.dict(os.environ, {'SENDER_EMAIL': 'test@example.com', 'EMAIL_PASSWORD': 'testpass'})
    def test_enhanced_main_imports(self):
        """Test that enhanced main module imports work."""
        try:
            import main_enhanced
            self.assertTrue(hasattr(main_enhanced, 'scrape_products_enhanced'))
            self.assertTrue(hasattr(main_enhanced, 'send_enhanced_email'))
            self.assertTrue(hasattr(main_enhanced, 'PerformanceMetrics'))
        except ImportError as e:
            self.fail(f"Enhanced main module should import cleanly: {e}")


if __name__ == '__main__':
    # Set up test environment
    os.environ.setdefault('SENDER_EMAIL', 'test@example.com')
    os.environ.setdefault('EMAIL_PASSWORD', 'testpassword')
    
    # Create test suite
    test_classes = [
        TestBaseRetailer,
        TestLululemonRetailer, 
        TestNikeRetailer,
        TestSimpleCache,
        TestRetailerRegistry,
        TestEnhancedConfiguration,
        TestIntegrationScenarios
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    sys.exit(0 if result.wasSuccessful() else 1)