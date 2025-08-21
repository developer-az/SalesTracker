"""
Enhanced command-line interface for Sale Tracker with new retailer framework.
"""

import argparse
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any

# Import enhanced modules
import main_enhanced
import config_enhanced as config
from retailers import registry
import recipients_store
import subscriptions_store


def setup_logging(verbose=False, quiet=False):
    """Set up logging configuration."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
        
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def test_enhanced_scraping(retailer_filter=None, use_cache=True):
    """Test enhanced scraping functionality with new framework."""
    print("🔍 Testing Enhanced Scraping Framework")
    print("=" * 60)
    
    # Show available retailers
    available_retailers = registry.get_supported_retailers()
    print(f"Available Retailers: {', '.join(available_retailers)}")
    print()
    
    # Get products to test
    product_links = config.PRODUCT_LINKS.copy()
    
    if retailer_filter:
        if retailer_filter in product_links:
            product_links = {retailer_filter: product_links[retailer_filter]}
            print(f"Testing only {retailer_filter} products")
        else:
            print(f"❌ Retailer '{retailer_filter}' not found. Available: {list(product_links.keys())}")
            return
    
    print(f"Cache enabled: {use_cache}")
    print()
    
    # Test scraping
    start_time = datetime.now()
    results = main_enhanced.scrape_products_enhanced(product_links)
    end_time = datetime.now()
    
    # Display results
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"📊 Results Summary:")
    print(f"   Total Products: {total_count}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {total_count - success_count}")
    print(f"   Duration: {(end_time - start_time).total_seconds():.2f}s")
    print()
    
    # Show detailed results
    print("📋 Detailed Results:")
    print("-" * 60)
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {result['retailer'].upper()}")
        print(f"   Name: {result['name']}")
        print(f"   Price: {result['price']}")
        print(f"   URL: {result['url']}")
        if result['image']:
            print(f"   Image: {result['image'][:80]}{'...' if len(result['image']) > 80 else ''}")
        print(f"   Timestamp: {result['timestamp']}")
        print()
    
    # Show cache statistics
    cache_stats = registry.get_cache_stats()
    if cache_stats['enabled']:
        print(f"💾 Cache Statistics:")
        print(f"   Cache Size: {cache_stats['size']} items")
        print(f"   Default TTL: {cache_stats['default_ttl']}s")


def show_enhanced_config():
    """Display enhanced configuration."""
    print("⚙️  Enhanced Configuration")
    print("=" * 60)
    
    full_config = config.get_config()
    
    # Show key sections
    sections = {
        'Product Links': full_config['product_links'],
        'Email Settings': full_config['email'],
        'Scraping Settings': full_config['scraping'],
        'Performance Settings': full_config['performance'],
        'Security Settings': full_config['security'],
        'Feature Flags': full_config['features'],
        'Retailer Settings': full_config['retailers']
    }
    
    for section_name, section_data in sections.items():
        print(f"\n📂 {section_name}:")
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, (list, dict)):
                    print(f"   {key}: {type(value).__name__} with {len(value)} items")
                else:
                    print(f"   {key}: {value}")
        else:
            print(f"   {section_data}")
    
    print(f"\n📋 System Info:")
    print(f"   Version: {full_config['version']}")
    print(f"   Last Updated: {full_config['last_updated']}")
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        print(f"\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"\n✅ Configuration is valid")


def send_test_email_enhanced(recipients=None):
    """Send enhanced test email."""
    print("📧 Sending Enhanced Test Email")
    print("=" * 40)
    
    try:
        if not recipients:
            try:
                _, _, recipients = main_enhanced.get_email_credentials()
            except ValueError:
                print("❌ No email credentials found in environment variables")
                return
        
        if not recipients:
            print("❌ No recipients specified")
            return
        
        print(f"Recipients: {', '.join(recipients)}")
        
        # Get sample products for test email
        print("Fetching sample product data...")
        sample_products = main_enhanced.scrape_products_enhanced()
        
        # Send test email
        main_enhanced.send_enhanced_email(sample_products, recipients)
        print("✅ Enhanced test email sent successfully!")
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")


def show_retailer_info():
    """Show detailed retailer information."""
    print("🏪 Retailer Information")
    print("=" * 40)
    
    retailers = registry.get_supported_retailers()
    
    for retailer_name in retailers:
        retailer = registry.get_retailer(retailer_name)
        if retailer:
            print(f"\n📦 {retailer_name.upper()}")
            metadata = retailer.get_metadata()
            print(f"   User Agent: {metadata['user_agent'][:50]}...")
            print(f"   Timeout: {metadata['timeout']}s")
            print(f"   Retry Attempts: {metadata['retry_attempts']}")
            
            # Get retailer-specific config
            retailer_config = config.get_retailer_config(retailer_name)
            if 'rate_limit' in retailer_config:
                print(f"   Rate Limit: {retailer_config['rate_limit']}s")
            if 'cache_ttl' in retailer_config:
                print(f"   Cache TTL: {retailer_config['cache_ttl']}s")
    
    print(f"\n📊 Cache Statistics:")
    cache_stats = registry.get_cache_stats()
    for key, value in cache_stats.items():
        print(f"   {key.title()}: {value}")


def manage_recipients(action, email=None):
    """Manage email recipients."""
    print(f"👥 Managing Recipients - {action.title()}")
    print("=" * 40)
    
    if action == "list":
        recipients = recipients_store.load_recipients()
        if recipients:
            print(f"Found {len(recipients)} recipients:")
            for i, email in enumerate(recipients, 1):
                print(f"  {i}. {email}")
        else:
            print("No recipients found.")
    
    elif action == "add":
        if not email:
            email = input("Enter email address: ").strip()
        
        if email:
            result = recipients_store.add_recipient(email)
            if result.get('success'):
                print(f"✅ Added recipient: {email}")
            else:
                print(f"❌ Failed to add recipient: {email} - {result.get('error', 'Unknown error')}")
        else:
            print("❌ No email provided")
    
    elif action == "remove":
        if not email:
            email = input("Enter email address to remove: ").strip()
        
        if email:
            result = recipients_store.remove_recipient(email)
            if result.get('success'):
                print(f"✅ Removed recipient: {email}")
            else:
                print(f"❌ Recipient not found: {email}")
        else:
            print("❌ No email provided")


def health_check():
    """Perform comprehensive health check."""
    print("🏥 System Health Check")
    print("=" * 40)
    
    issues = []
    
    # Check configuration
    print("Checking configuration...")
    config_issues = config.validate_config()
    if config_issues:
        issues.extend(config_issues)
        print(f"❌ Configuration issues: {len(config_issues)}")
        for issue in config_issues:
            print(f"   - {issue}")
    else:
        print("✅ Configuration is valid")
    
    # Check retailers
    print("\nChecking retailer registry...")
    retailers = registry.get_supported_retailers()
    if retailers:
        print(f"✅ {len(retailers)} retailers available: {', '.join(retailers)}")
    else:
        issues.append("No retailers registered")
        print("❌ No retailers available")
    
    # Check storage
    print("\nChecking storage systems...")
    try:
        recipients = recipients_store.load_recipients()
        print(f"✅ Recipients storage working ({len(recipients)} recipients)")
    except Exception as e:
        issues.append(f"Recipients storage error: {e}")
        print(f"❌ Recipients storage error: {e}")
    
    try:
        subscriptions = subscriptions_store.list_all_subscriptions()
        print(f"✅ Subscriptions storage working ({len(subscriptions)} subscriptions)")
    except Exception as e:
        issues.append(f"Subscriptions storage error: {e}")
        print(f"❌ Subscriptions storage error: {e}")
    
    # Check email credentials
    print("\nChecking email configuration...")
    try:
        main_enhanced.get_email_credentials()
        print("✅ Email credentials available")
    except Exception as e:
        issues.append(f"Email credentials error: {e}")
        print(f"❌ Email credentials error: {e}")
    
    # Summary
    print(f"\n{'='*40}")
    if not issues:
        print("🎉 All systems healthy!")
        return True
    else:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False


def run_enhanced_scheduler():
    """Run the enhanced scheduler."""
    print("🚀 Starting Enhanced Sale Tracker Scheduler")
    print("=" * 50)
    
    # Perform initial health check
    if not health_check():
        print("\n⚠️  Health check failed. Starting anyway...")
        
    print("\n🕐 Starting scheduler...")
    print("Press Ctrl+C to stop")
    
    try:
        main_enhanced.run_enhanced_scheduler()
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced Sale Tracker CLI with new retailer framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s test-scraping                    # Test all retailers
  %(prog)s test-scraping --retailer nike    # Test only Nike
  %(prog)s test-scraping --no-cache         # Test without cache
  %(prog)s send-test --recipients user@example.com
  %(prog)s config                           # Show configuration
  %(prog)s retailers                        # Show retailer info
  %(prog)s recipients list                  # List recipients
  %(prog)s recipients add user@example.com  # Add recipient
  %(prog)s health                           # Health check
  %(prog)s run                              # Start scheduler
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output (errors only)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test scraping command
    scrape_parser = subparsers.add_parser('test-scraping', help='Test scraping functionality')
    scrape_parser.add_argument('--retailer', help='Test specific retailer only')
    scrape_parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    
    # Send test email command
    email_parser = subparsers.add_parser('send-test', help='Send test email')
    email_parser.add_argument('--recipients', nargs='+', help='Email recipients')
    
    # Configuration command
    subparsers.add_parser('config', help='Show configuration')
    
    # Retailer info command
    subparsers.add_parser('retailers', help='Show retailer information')
    
    # Recipients management
    recipients_parser = subparsers.add_parser('recipients', help='Manage email recipients')
    recipients_parser.add_argument('action', choices=['list', 'add', 'remove'], help='Action to perform')
    recipients_parser.add_argument('email', nargs='?', help='Email address')
    
    # Health check command
    subparsers.add_parser('health', help='Perform system health check')
    
    # Run scheduler command
    subparsers.add_parser('run', help='Start the enhanced scheduler')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose, args.quiet)
    
    # Execute commands
    if args.command == 'test-scraping':
        test_enhanced_scraping(
            retailer_filter=args.retailer,
            use_cache=not args.no_cache
        )
    elif args.command == 'send-test':
        send_test_email_enhanced(args.recipients)
    elif args.command == 'config':
        show_enhanced_config()
    elif args.command == 'retailers':
        show_retailer_info()
    elif args.command == 'recipients':
        manage_recipients(args.action, args.email)
    elif args.command == 'health':
        success = health_check()
        sys.exit(0 if success else 1)
    elif args.command == 'run':
        run_enhanced_scheduler()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()