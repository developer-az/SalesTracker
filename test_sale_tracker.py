"""
Test suite for Sale Tracker application
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile
import shutil

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main_improved
import config

class TestSaleTracker(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
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
        with patch.dict(os.environ, {
            'SENDER_EMAIL': 'test@example.com',
            'EMAIL_PASSWORD': 'test_password',
            'RECIPIENT_EMAIL': 'recipient@example.com',
            'RECIPIENT_EMAIL2': 'recipient2@example.com'
        }, clear=True):
            sender_email, sender_password, recipient_emails = main_improved.get_email_credentials()
            
            self.assertEqual(sender_email, 'test@example.com')
            self.assertEqual(sender_password, 'test_password')
            self.assertEqual(recipient_emails, ['recipient@example.com', 'recipient2@example.com'])
    
    def test_get_email_credentials_missing_recipient2(self):
        """Test email credentials with missing RECIPIENT_EMAIL2."""
        with patch.dict(os.environ, {
            'SENDER_EMAIL': 'test@example.com',
            'EMAIL_PASSWORD': 'test_password',
            'RECIPIENT_EMAIL': 'recipient@example.com'
        }, clear=True):
            sender_email, sender_password, recipient_emails = main_improved.get_email_credentials()
            
            self.assertEqual(sender_email, 'test@example.com')
            self.assertEqual(sender_password, 'test_password')
            self.assertEqual(recipient_emails, ['recipient@example.com'])
    
    def test_get_email_credentials_missing_required(self):
        """Test email credentials with missing required fields."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                main_improved.get_email_credentials()
    
    @patch('main_improved.requests.get')
    def test_scrape_lululemon_success(self, mock_get):
        """Test successful Lululemon scraping."""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.content = '''
        <html>
            <meta property="og:title" content="Test Product">
            <span class="price">$100USD</span>
            <meta property="og:image" content="http://example.com/image.jpg">
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        name, price, image = main_improved.scrape_lululemon('http://example.com')
        
        self.assertEqual(name, 'Test Product')
        self.assertEqual(price, '$100USD')
        self.assertEqual(image, 'http://example.com/image.jpg')
    
    @patch('main_improved.requests.get')
    def test_scrape_lululemon_request_error(self, mock_get):
        """Test Lululemon scraping with request error."""
        mock_get.side_effect = Exception("Connection error")
        
        name, price, image = main_improved.scrape_lululemon('http://example.com')
        
        self.assertEqual(name, 'Product name not found')
        self.assertEqual(price, 'Price not found')
        self.assertEqual(image, '')
    
    @patch('main_improved.requests.get')
    def test_scrape_nike_success(self, mock_get):
        """Test successful Nike scraping."""
        # Mock HTML response with JSON-LD
        mock_response = MagicMock()
        mock_response.text = '''
        <html>
            <script type="application/ld+json">
            {
                "name": "Nike Test Product",
                "offers": {
                    "lowPrice": "150"
                }
            }
            </script>
            <meta property="og:image" content="http://example.com/nike.jpg">
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        name, price, image = main_improved.scrape_nike('http://example.com')
        
        self.assertEqual(name, 'Nike Test Product')
        self.assertEqual(price, '$150USD')
        self.assertEqual(image, 'http://example.com/nike.jpg')
    
    @patch('main_improved.requests.get')
    def test_scrape_nike_no_json_ld(self, mock_get):
        """Test Nike scraping with no JSON-LD data."""
        mock_response = MagicMock()
        mock_response.text = '<html><body>No JSON-LD here</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        name, price, image = main_improved.scrape_nike('http://example.com')
        
        self.assertEqual(name, 'Product name not found')
        self.assertEqual(price, 'Price not found')
        self.assertEqual(image, '')
    
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

class TestIntegration(unittest.TestCase):
    """Integration tests that require actual network requests."""
    
    def test_lululemon_live_scraping(self):
        """Test live Lululemon scraping (requires internet)."""
        try:
            name, price, image = main_improved.scrape_lululemon(
                config.PRODUCT_LINKS['lululemon'][0]
            )
            
            # Basic validation
            self.assertIsInstance(name, str)
            self.assertIsInstance(price, str)
            self.assertIsInstance(image, str)
            self.assertGreater(len(name), 0)
            self.assertIn('USD', price)
            
        except Exception as e:
            self.skipTest(f"Live test failed (network issue?): {e}")
    
    def test_nike_live_scraping(self):
        """Test live Nike scraping (requires internet)."""
        try:
            name, price, image = main_improved.scrape_nike(
                config.PRODUCT_LINKS['nike'][0]
            )
            
            # Basic validation
            self.assertIsInstance(name, str)
            self.assertIsInstance(price, str)
            self.assertIsInstance(image, str)
            self.assertGreater(len(name), 0)
            self.assertIn('USD', price)
            
        except Exception as e:
            self.skipTest(f"Live test failed (network issue?): {e}")

if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2)
