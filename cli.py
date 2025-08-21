#!/usr/bin/env python3
"""
Command-line interface for Sale Tracker
"""

import argparse
import sys
import logging
from datetime import datetime
import main_improved
import config

def setup_logging(verbose=False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sale_tracker.log'),
            logging.StreamHandler()
        ]
    )

def test_scraping():
    """Test scraping functionality."""
    print("Testing scraping functionality...")
    print("=" * 50)
    
    for company, links in config.PRODUCT_LINKS.items():
        print(f"\n{company.upper()}:")
        for i, link in enumerate(links, 1):
            print(f"  Product {i}:")
            try:
                if company == "lululemon":
                    name, price, image = main_improved.scrape_lululemon(link)
                elif company == "nike":
                    name, price, image = main_improved.scrape_nike(link)
                else:
                    print(f"    Unknown company: {company}")
                    continue
                
                print(f"    Name: {name}")
                print(f"    Price: {price}")
                print(f"    Image: {image[:50]}..." if image else "    Image: Not found")
                print(f"    Link: {link}")
                
            except Exception as e:
                print(f"    Error: {e}")

def send_test_email():
    """Send a test email."""
    print("Sending test email...")
    try:
        main_improved.send_combined_email()
        print("Test email sent successfully!")
    except Exception as e:
        print(f"Failed to send test email: {e}")
        sys.exit(1)

def show_config():
    """Display current configuration."""
    print("Current Configuration:")
    print("=" * 50)
    
    print(f"\nEmail Settings:")
    for key, value in config.EMAIL_SETTINGS.items():
        print(f"  {key}: {value}")
    
    print(f"\nScraping Settings:")
    for key, value in config.SCRAPING_SETTINGS.items():
        print(f"  {key}: {value}")
    
    print(f"\nProduct Links:")
    for company, links in config.PRODUCT_LINKS.items():
        print(f"  {company}:")
        for i, link in enumerate(links, 1):
            print(f"    {i}. {link}")

def run_scheduler():
    """Run the scheduler."""
    print(f"Starting Sale Tracker scheduler...")
    print(f"Emails will be sent daily at {config.EMAIL_SETTINGS['schedule_time']}")
    print("Press Ctrl+C to stop")
    
    try:
        main_improved.run_scheduler()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        print(f"Scheduler error: {e}")
        sys.exit(1)

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Sale Tracker - Email Notifier for Product Price Tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s test-scraping     # Test scraping functionality
  %(prog)s send-test         # Send a test email
  %(prog)s show-config       # Display current configuration
  %(prog)s run               # Start the scheduler
  %(prog)s run --verbose     # Start scheduler with verbose logging
        """
    )
    
    parser.add_argument(
        'command',
        choices=['test-scraping', 'send-test', 'show-config', 'run'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'test-scraping':
        test_scraping()
    elif args.command == 'send-test':
        send_test_email()
    elif args.command == 'show-config':
        show_config()
    elif args.command == 'run':
        run_scheduler()

if __name__ == '__main__':
    main()
