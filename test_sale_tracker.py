"""
Test suite for Sale Tracker application
"""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import main_improved
import recipients_store
import scraper


class TestSaleTracker(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        recipients_store.RECIPIENTS_FILE = os.path.join(self.test_dir, "recipients.json")

        # Create a test .env file
        self.env_content = """SENDER_EMAIL=test@example.com
EMAIL_PASSWORD=test_password
RECIPIENT_EMAIL=recipient@example.com
RECIPIENT_EMAIL2=recipient2@example.com"""

        with open('.env', 'w') as f:
            f.write(self.env_content)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_get_email_credentials_success(self):
        """Test successful email credentials retrieval."""
        with patch.dict(
            os.environ,
            {
                'SENDER_EMAIL': 'test@example.com',
                'EMAIL_PASSWORD': 'test_password',
                'RECIPIENT_EMAIL': 'recipient@example.com',
                'RECIPIENT_EMAIL2': 'recipient2@example.com',
            },
            clear=True,
        ):
            sender_email, sender_password, recipient_emails = main_improved.get_email_credentials()

            self.assertEqual(sender_email, 'test@example.com')
            self.assertEqual(sender_password, 'test_password')
            self.assertEqual(recipient_emails, ['recipient@example.com', 'recipient2@example.com'])

    def test_get_email_credentials_missing_recipient2(self):
        """Test email credentials with missing RECIPIENT_EMAIL2."""
        with patch.dict(
            os.environ,
            {
                'SENDER_EMAIL': 'test@example.com',
                'EMAIL_PASSWORD': 'test_password',
                'RECIPIENT_EMAIL': 'recipient@example.com',
            },
            clear=True,
        ):
            sender_email, sender_password, recipient_emails = main_improved.get_email_credentials()

            self.assertEqual(sender_email, 'test@example.com')
            self.assertEqual(sender_password, 'test_password')
            self.assertEqual(recipient_emails, ['recipient@example.com'])

    def test_get_email_credentials_missing_required(self):
        """Test email credentials with missing required fields."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                main_improved.get_email_credentials()

    def test_parse_og_and_price_markup(self):
        """A simple storefront page: og tags plus a price element."""
        html = """
        <html>
            <head>
                <meta property="og:title" content="Test Product">
                <meta property="og:image" content="http://example.com/image.jpg">
                <title>Test Product | Example</title>
            </head>
            <body><span class="price">$100.00 USD</span></body>
        </html>
        """
        result = scraper.parse_product(html, "https://example.com/p/test-product")

        self.assertEqual(result["name"], "Test Product")
        self.assertEqual(result["price"], 100.0)
        self.assertEqual(result["price_display"], "$100.00")
        self.assertEqual(result["image"], "http://example.com/image.jpg")
        self.assertTrue(result["success"])

    def test_parse_nike_product_group(self):
        """Nike publishes a ProductGroup with variant offers."""
        html = """
        <html><head><title>Nike Test Product. Nike.com</title></head><body>
            <script type="application/ld+json">
            {
                "@type": "ProductGroup",
                "name": "Nike Test Product",
                "hasVariant": [
                    {"@type": "Product", "name": "Nike Test Product - Black - Size S",
                     "offers": {"@type": "Offer", "price": "150.00", "priceCurrency": "USD"}}
                ]
            }
            </script>
        </body></html>
        """
        result = scraper.parse_product(html, "https://www.nike.com/t/nike-test-product/ABC123")

        self.assertEqual(result["name"], "Nike Test Product")
        self.assertEqual(result["price"], 150.0)
        self.assertEqual(result["price_display"], "$150.00")
        self.assertEqual(result["retailer"], "Nike")
        self.assertTrue(result["success"])

    def test_parse_page_without_product_data(self):
        html = "<html><body><h1>No product data here</h1></body></html>"
        result = scraper.parse_product(html, "https://example.com/p/plain-page")

        self.assertFalse(result["success"])
        self.assertIsNone(result["price"])
        self.assertEqual(result["status"], "price_missing")

    def test_blocked_page_is_detected(self):
        html = "<html><head><title>Access Denied</title></head><body>Access Denied</body></html>"
        self.assertTrue(scraper._looks_blocked(html, 200))
        self.assertTrue(scraper._looks_blocked("", 403))
        self.assertFalse(scraper._looks_blocked("<html><title>Product</title></html>", 200))

    def test_name_from_blocked_url(self):
        url = "https://shop.lululemon.com/p/mens-jackets-and-outerwear/" "Down-For-It-All-Hoodie/_/prod9200786?color=0001"
        self.assertEqual(scraper._name_from_url(url), "Down For It All Hoodie")

    def test_config_structure(self):
        """Test that config file has required structure."""
        self.assertIn('lululemon', config.PRODUCT_LINKS)
        self.assertIn('nike', config.PRODUCT_LINKS)
        self.assertIn('smtp_server', config.EMAIL_SETTINGS)
        self.assertIn('smtp_port', config.EMAIL_SETTINGS)
        self.assertIn('schedule_time', config.EMAIL_SETTINGS)
        self.assertIn('timeout', config.SCRAPING_SETTINGS)
        self.assertIn('user_agent', config.SCRAPING_SETTINGS)

    def test_config_values(self):
        """Test that config values are reasonable."""
        self.assertEqual(config.EMAIL_SETTINGS['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(config.EMAIL_SETTINGS['smtp_port'], 587)
        self.assertGreater(config.SCRAPING_SETTINGS['timeout'], 0)
        self.assertIsInstance(config.SCRAPING_SETTINGS['user_agent'], str)
        self.assertGreater(len(config.SCRAPING_SETTINGS['user_agent']), 0)


RUN_NETWORK_TESTS = os.environ.get("RUN_NETWORK_TESTS", "").lower() in {"1", "true", "yes"}


@unittest.skipUnless(RUN_NETWORK_TESTS, "network tests: set RUN_NETWORK_TESTS=1 to run")
class TestIntegration(unittest.TestCase):
    """Integration tests that require actual network requests."""

    def test_nike_live_scraping(self):
        """Nike should return a real product name and price."""
        result = scraper.scrape(
            "https://www.nike.com/t/unlimited-mens-repel-hooded-versatile-jacket-56pDjs/FB7551-010",
            force=True,
        )
        self.assertTrue(result["name"])
        self.assertIn(result["status"], ["ok", "blocked", "price_missing"])
        if result["status"] == "ok":
            self.assertIsNotNone(result["price"])
            self.assertTrue(result["price_display"].startswith("$"))

    def test_lululemon_live_scraping(self):
        """Lululemon may block datacenter IPs, but should fail gracefully."""
        result = scraper.scrape(
            "https://shop.lululemon.com/p/mens-jackets-and-outerwear/" "Down-For-It-All-Hoodie/_/prod9200786?color=0001",
            force=True,
        )
        self.assertTrue(result["name"])
        self.assertIn(result["status"], ["ok", "blocked", "price_missing"])


if __name__ == '__main__':
    unittest.main(verbosity=2)
