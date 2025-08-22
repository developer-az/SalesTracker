"""
Enhanced Sale Tracker with new retailer framework and performance improvements.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import schedule
import time
import sys
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import json

# Import the new retailer framework
from retailers import registry
import config_enhanced as config
import recipients_store
import subscriptions_store

# Set up enhanced logging
def setup_logging():
    """Set up enhanced logging with rotation and structured format."""
    log_level = getattr(logging, config.PERFORMANCE_SETTINGS.get("log_level", "INFO"))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Create handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler with rotation
    if config.PERFORMANCE_SETTINGS.get("enable_structured_logging", True):
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                'sale_tracker_enhanced.log',
                maxBytes=config.PERFORMANCE_SETTINGS.get("max_log_file_size", 10*1024*1024),
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except ImportError:
            # Fallback to regular file handler
            file_handler = logging.FileHandler('sale_tracker_enhanced.log')
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True
    )

setup_logging()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Performance tracking
class PerformanceMetrics:
    """Simple performance metrics tracking."""
    
    def __init__(self):
        self.metrics = {
            'scrapes_total': 0,
            'scrapes_successful': 0,
            'scrapes_failed': 0,
            'emails_sent': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_scrape_time': 0.0,
            'last_updated': datetime.now()
        }
        self.scrape_times = []
    
    def record_scrape(self, success: bool, duration: float):
        """Record a scraping operation."""
        self.metrics['scrapes_total'] += 1
        if success:
            self.metrics['scrapes_successful'] += 1
        else:
            self.metrics['scrapes_failed'] += 1
        
        self.scrape_times.append(duration)
        # Keep only last 100 measurements for rolling average
        if len(self.scrape_times) > 100:
            self.scrape_times.pop(0)
        
        self.metrics['avg_scrape_time'] = sum(self.scrape_times) / len(self.scrape_times)
        self.metrics['last_updated'] = datetime.now()
    
    def record_email_sent(self):
        """Record an email sent."""
        self.metrics['emails_sent'] += 1
        self.metrics['last_updated'] = datetime.now()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()

# Global metrics instance
metrics = PerformanceMetrics() if config.PERFORMANCE_SETTINGS.get("enable_metrics") else None


def get_email_credentials() -> Tuple[str, str, List[str]]:
    """Get email credentials from environment variables with fallbacks."""
    sender_email = os.getenv("SENDER_EMAIL")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not email_password:
        logger.error("Missing required email credentials in environment variables")
        raise ValueError("Missing email credentials")
    
    # Get recipient emails with fallback
    recipients = []
    recipient1 = os.getenv("RECIPIENT_EMAIL")
    recipient2 = os.getenv("RECIPIENT_EMAIL2")
    
    if recipient1:
        recipients.append(recipient1)
    if recipient2:
        recipients.append(recipient2)
    
    if not recipients:
        logger.warning("No recipient emails found in environment variables")
    
    return sender_email, email_password, recipients


def scrape_products_enhanced(product_links: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, Any]]:
    """Enhanced product scraping using the new retailer framework."""
    if product_links is None:
        product_links = config.PRODUCT_LINKS
    
    # Flatten product links to a single list with metadata
    all_urls = []
    for retailer, urls in product_links.items():
        for url in urls:
            all_urls.append(url)
    
    logger.info(f"Scraping {len(all_urls)} products using enhanced retailer framework")
    
    # Use the retailer registry to scrape all products
    start_time = time.time()
    results = registry.scrape_multiple(
        all_urls,
        use_cache=config.SCRAPING_SETTINGS.get("enable_cache", True),
        delay=config.SCRAPING_SETTINGS.get("rate_limit_delay", 1.0)
    )
    end_time = time.time()
    
    # Record metrics
    if metrics:
        total_duration = end_time - start_time
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        for _ in range(successful):
            metrics.record_scrape(True, total_duration / len(results))
        for _ in range(failed):
            metrics.record_scrape(False, total_duration / len(results))
    
    logger.info(f"Scraping completed in {end_time - start_time:.2f}s. "
                f"Success: {sum(1 for r in results if r['success'])}, "
                f"Failed: {sum(1 for r in results if not r['success'])}")
    
    # Log cache statistics
    cache_stats = registry.get_cache_stats()
    if cache_stats['enabled']:
        logger.debug(f"Cache stats: {cache_stats}")
    
    return results


def create_enhanced_email_content(products: List[Dict[str, Any]], recipient: str) -> str:
    """Create enhanced HTML email content."""
    current_date = datetime.now().strftime("%B %d, %Y")
    successful_products = [p for p in products if p['success']]
    failed_products = [p for p in products if not p['success']]
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; }}
            .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .product-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .product-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fafafa; }}
            .product-image {{ width: 100%; max-width: 200px; height: auto; border-radius: 5px; }}
            .product-name {{ font-size: 16px; font-weight: bold; margin: 10px 0; color: #333; }}
            .product-price {{ font-size: 18px; color: #e74c3c; font-weight: bold; }}
            .product-retailer {{ background-color: #3498db; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; display: inline-block; margin-top: 5px; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
            .metrics {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .error-section {{ background-color: #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛍️ Your Daily Product Updates</h1>
                <p>{current_date}</p>
            </div>
            
            <p>Hi there! Here's your daily product price update.</p>
            
            <div class="metrics">
                <h3>📊 Summary</h3>
                <p><strong>Total Products:</strong> {len(products)} | <strong>Successfully Updated:</strong> {len(successful_products)} | <strong>Failed:</strong> {len(failed_products)}</p>
                {f"<p><strong>Cache Hits:</strong> {registry.get_cache_stats()['size']} items cached</p>" if registry.get_cache_stats()['enabled'] else ""}
            </div>
    """
    
    if successful_products:
        html_content += '<div class="product-grid">'
        for product in successful_products:
            html_content += f'''
            <div class="product-card">
                <div class="product-retailer">{product['retailer'].title()}</div>
                {f'<img src="{product["image"]}" alt="Product Image" class="product-image" onerror="this.style.display=\'none\'">' if product.get('image') else ''}
                <div class="product-name">{product['name']}</div>
                <div class="product-price">{product['price']}</div>
                <p><a href="{product['url']}" target="_blank" style="color: #3498db;">View Product →</a></p>
                <small style="color: #7f8c8d;">Updated: {product['timestamp'][:16]}</small>
            </div>
            '''
        html_content += '</div>'
    
    if failed_products:
        html_content += f'''
        <div class="error-section">
            <h3>⚠️ Failed to Update ({len(failed_products)} products)</h3>
            <ul>
        '''
        for product in failed_products:
            html_content += f'<li><a href="{product["url"]}" target="_blank">{product["url"]}</a> - {product["name"]}</li>'
        html_content += '</ul></div>'
    
    html_content += f'''
            <div class="footer">
                <p>This email was generated automatically by Sale Tracker v{config.get_config()["version"]}</p>
                <p>Powered by Enhanced Retailer Framework</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html_content


def send_enhanced_email(products: List[Dict[str, Any]], recipients: List[str]):
    """Send enhanced email with product information."""
    try:
        sender_email, email_password, _ = get_email_credentials()
        
        # Create subject line based on successful products
        successful_products = [p for p in products if p['success']]
        total_products = len(products)
        subject = f"Daily Product Update - {len(successful_products)}/{total_products} products updated"
        
        for recipient in recipients:
            try:
                msg = MIMEMultipart('alternative')
                msg["From"] = sender_email
                msg["To"] = recipient
                msg["Subject"] = subject
                
                # Create enhanced HTML content
                html_content = create_enhanced_email_content(products, recipient)
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
                
                # Send email with retry logic
                max_retries = config.EMAIL_SETTINGS.get("max_retries", 3)
                retry_delay = config.EMAIL_SETTINGS.get("retry_delay", 5)
                
                for attempt in range(max_retries):
                    try:
                        with smtplib.SMTP(config.EMAIL_SETTINGS["smtp_server"], config.EMAIL_SETTINGS["smtp_port"]) as server:
                            server.starttls()
                            server.login(sender_email, email_password)
                            server.sendmail(sender_email, recipient, msg.as_string())
                        
                        logger.info(f"Enhanced email sent successfully to {recipient}")
                        if metrics:
                            metrics.record_email_sent()
                        break
                        
                    except smtplib.SMTPException as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Email attempt {attempt + 1} failed to {recipient}: {e}. Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                        else:
                            logger.error(f"Failed to send email to {recipient} after {max_retries} attempts: {e}")
                            
            except Exception as e:
                logger.error(f"Error preparing email for {recipient}: {e}")
                
    except Exception as e:
        logger.error(f"Error in send_enhanced_email: {e}")


def run_enhanced_scheduler():
    """Enhanced scheduler with error handling and metrics."""
    logger.info("Starting Enhanced Sale Tracker with new retailer framework")
    logger.info(f"Configuration: {len(config.PRODUCT_LINKS)} retailers, "
                f"{sum(len(urls) for urls in config.PRODUCT_LINKS.values())} total products")
    logger.info(f"Cache enabled: {config.SCRAPING_SETTINGS.get('enable_cache')}")
    logger.info(f"Supported retailers: {registry.get_supported_retailers()}")
    
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        logger.error("Configuration issues found:")
        for issue in config_issues:
            logger.error(f"  - {issue}")
        if "Missing required environment variable" in str(config_issues):
            logger.error("Cannot continue without required environment variables")
            return
    
    # Schedule daily email
    schedule.every().day.at(config.EMAIL_SETTINGS["schedule_time"]).do(send_daily_email_enhanced)
    logger.info(f"Scheduled daily emails at {config.EMAIL_SETTINGS['schedule_time']}")
    
    # Health check scheduling
    if config.PERFORMANCE_SETTINGS.get("health_check_interval"):
        schedule.every(config.PERFORMANCE_SETTINGS["health_check_interval"]).seconds.do(health_check)
    
    # Main scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


def send_daily_email_enhanced():
    """Enhanced daily email function."""
    logger.info("Starting enhanced daily email process")
    
    try:
        # Scrape all products
        products = scrape_products_enhanced()
        
        # Get recipients from both environment and storage
        try:
            _, _, env_recipients = get_email_credentials()
        except ValueError:
            env_recipients = []
        
        # Get recipients from storage
        storage_recipients = recipients_store.load_recipients()
        
        # Combine and deduplicate recipients
        all_recipients = list(set(env_recipients + storage_recipients))
        
        if not all_recipients:
            logger.warning("No recipients found. Email not sent.")
            return
        
        # Send enhanced emails
        send_enhanced_email(products, all_recipients)
        
        logger.info(f"Enhanced daily email process completed. Sent to {len(all_recipients)} recipients.")
        
    except Exception as e:
        logger.error(f"Error in enhanced daily email process: {e}")


def health_check():
    """Perform health check and log system status."""
    try:
        # Check retailer registry
        retailers = registry.get_supported_retailers()
        cache_stats = registry.get_cache_stats()
        
        # Check configuration
        config_issues = config.validate_config()
        
        # Get metrics
        current_metrics = metrics.get_metrics() if metrics else {}
        
        health_info = {
            "timestamp": datetime.now().isoformat(),
            "retailers_available": len(retailers),
            "retailers": retailers,
            "cache_enabled": cache_stats['enabled'],
            "cache_size": cache_stats.get('size', 0),
            "config_issues": len(config_issues),
            "metrics": current_metrics,
            "status": "healthy" if not config_issues else "degraded"
        }
        
        logger.info(f"Health check: {json.dumps(health_info, indent=2)}")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")


if __name__ == '__main__':
    try:
        run_enhanced_scheduler()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)