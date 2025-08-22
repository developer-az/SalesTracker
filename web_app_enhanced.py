"""
Enhanced web application with new retailer framework and improved UI.
"""

import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import threading
import time
import json
import logging

# Import enhanced modules
import main_enhanced
import config_enhanced as config
from retailers import registry
import recipients_store
import subscriptions_store

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment settings
CRON_TOKEN = os.environ.get('CRON_TOKEN', '1')

class EnhancedWebAppState:
    """Enhanced application state management."""
    def __init__(self):
        self.last_scrape_results = []
        self.is_running = False
        self.last_email_sent = None
        self.scheduler_thread = None
        self.performance_metrics = {}
        self.system_status = "starting"
        
    def update_scrape_results(self, results):
        """Update scrape results and metrics."""
        self.last_scrape_results = results
        
        # Update performance metrics
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        self.performance_metrics.update({
            'last_scrape_time': datetime.now().isoformat(),
            'total_products': len(results),
            'successful_scrapes': successful,
            'failed_scrapes': failed,
            'success_rate': (successful / len(results) * 100) if results else 0
        })
    
    def get_system_info(self):
        """Get comprehensive system information."""
        return {
            'status': self.system_status,
            'is_running': self.is_running,
            'last_email_sent': self.last_email_sent,
            'last_scrape_results': self.last_scrape_results,
            'performance_metrics': self.performance_metrics,
            'supported_retailers': registry.get_supported_retailers(),
            'cache_stats': registry.get_cache_stats(),
            'config_version': config.get_config()['version'],
            'timestamp': datetime.now().isoformat()
        }

# Global app state
app_state = EnhancedWebAppState()


@app.route('/')
def enhanced_dashboard():
    """Enhanced dashboard with new features."""
    scheduler_text = "Scheduled via GitHub Actions" if CRON_TOKEN else None
    
    # Get enhanced system info
    system_info = app_state.get_system_info()
    
    return render_template('enhanced_dashboard.html', 
                         products=app_state.last_scrape_results,
                         is_running=app_state.is_running,
                         last_email=app_state.last_email_sent,
                         config=config,
                         scheduler_text=scheduler_text,
                         system_info=system_info,
                         retailers=registry.get_supported_retailers(),
                         cache_stats=registry.get_cache_stats())


@app.route('/api/enhanced/scrape')
def api_enhanced_scrape():
    """Enhanced API endpoint to scrape all products using new framework."""
    try:
        logger.info("Starting enhanced scraping via API")
        
        # Use the new enhanced scraping
        results = main_enhanced.scrape_products_enhanced()
        
        # Update app state
        app_state.update_scrape_results(results)
        app_state.system_status = "healthy"
        
        # Return enhanced response
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total': len(results),
                'successful': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success']),
                'retailers': list(set(r['retailer'] for r in results))
            },
            'cache_stats': registry.get_cache_stats(),
            'performance_metrics': app_state.performance_metrics
        }
        
        logger.info(f"Enhanced scraping completed: {response['summary']}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Enhanced scraping failed: {e}")
        app_state.system_status = "error"
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/enhanced/retailers')
def api_enhanced_retailers():
    """Get detailed information about supported retailers."""
    try:
        retailers_info = {}
        
        for retailer_name in registry.get_supported_retailers():
            retailer = registry.get_retailer(retailer_name)
            if retailer:
                retailers_info[retailer_name] = {
                    'metadata': retailer.get_metadata(),
                    'config': config.get_retailer_config(retailer_name),
                    'supported_urls_pattern': f"*{retailer_name}*"
                }
        
        return jsonify({
            'success': True,
            'retailers': retailers_info,
            'cache_stats': registry.get_cache_stats(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting retailer info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enhanced/health')
def api_enhanced_health():
    """Enhanced health check endpoint."""
    try:
        health_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system_info': app_state.get_system_info(),
            'configuration': {
                'version': config.get_config()['version'],
                'issues': config.validate_config()
            },
            'retailers': {
                'available': registry.get_supported_retailers(),
                'cache_enabled': registry.get_cache_stats()['enabled']
            },
            'storage': {
                'recipients_count': len(recipients_store.load_recipients()),
                'subscriptions_count': len(subscriptions_store.list_all_subscriptions())
            }
        }
        
        # Determine overall health status
        config_issues = config.validate_config()
        if config_issues:
            health_info['status'] = 'degraded'
            health_info['issues'] = config_issues
        
        status_code = 200 if health_info['status'] == 'healthy' else 503
        return jsonify(health_info), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.route('/api/enhanced/metrics')
def api_enhanced_metrics():
    """Get performance metrics and statistics."""
    try:
        metrics = {
            'performance': app_state.performance_metrics,
            'cache': registry.get_cache_stats(),
            'system': app_state.get_system_info(),
            'configuration': {
                'retailers_count': len(registry.get_supported_retailers()),
                'total_product_links': sum(len(urls) for urls in config.PRODUCT_LINKS.values()),
                'features_enabled': sum(1 for enabled in config.FEATURE_FLAGS.values() if enabled)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enhanced/cache', methods=['GET', 'DELETE'])
def api_enhanced_cache():
    """Manage the retailer cache."""
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'cache_stats': registry.get_cache_stats(),
                'timestamp': datetime.now().isoformat()
            })
        
        elif request.method == 'DELETE':
            registry.clear_cache()
            return jsonify({
                'success': True,
                'message': 'Cache cleared successfully',
                'cache_stats': registry.get_cache_stats(),
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Cache operation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enhanced/test-retailer', methods=['POST'])
def api_test_retailer():
    """Test scraping a specific URL with a retailer."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # Find appropriate retailer
        retailer = registry.get_retailer_for_url(url)
        if not retailer:
            return jsonify({
                'success': False,
                'error': f'No retailer found for URL: {url}',
                'supported_retailers': registry.get_supported_retailers()
            }), 400
        
        # Test scraping
        start_time = time.time()
        name, price, image = registry.scrape_product(url, use_cache=False)  # Force fresh scrape
        end_time = time.time()
        
        result = {
            'success': name != "Product name not found",
            'retailer': retailer.name,
            'url': url,
            'name': name,
            'price': price,
            'image': image,
            'scrape_time': round(end_time - start_time, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Retailer test failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Keep the original endpoints for backward compatibility
@app.route('/api/cron/send', methods=['POST'])
def api_cron_send():
    """Secure endpoint for external cron (e.g., GitHub Actions) to trigger daily emails."""
    cron_token = request.headers.get('X-CRON-TOKEN')
    if cron_token != CRON_TOKEN:
        logger.warning(f"Unauthorized cron attempt from {request.remote_addr}")
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        logger.info("Cron-triggered enhanced daily email starting...")
        main_enhanced.send_daily_email_enhanced()
        app_state.last_email_sent = datetime.now().isoformat()
        return jsonify({
            'success': True,
            'message': 'Enhanced daily emails sent successfully',
            'timestamp': app_state.last_email_sent
        })
    except Exception as e:
        logger.error(f"Cron email send failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape')
def api_scrape():
    """Legacy API endpoint for backward compatibility."""
    return api_enhanced_scrape()


@app.route('/api/status')
def api_status():
    """API endpoint to get application status."""
    return jsonify(app_state.get_system_info())


@app.route('/api/config')
def api_config():
    """API endpoint to get current configuration."""
    try:
        return jsonify({
            'success': True,
            'config': config.get_config(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recipients', methods=['GET', 'POST', 'DELETE'])
def api_recipients():
    """Enhanced recipients management API."""
    try:
        if request.method == 'GET':
            recipients = recipients_store.load_recipients()
            return jsonify({
                'success': True,
                'recipients': [{'email': email} for email in recipients],
                'count': len(recipients)
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            email = data.get('email', '').strip()
            
            result = recipients_store.add_recipient(email)
            return jsonify(result), 200 if result['success'] else 400
        
        elif request.method == 'DELETE':
            data = request.get_json()
            email = data.get('email', '').strip()
            
            result = recipients_store.remove_recipient(email)
            return jsonify(result), 200 if result['success'] else 404
            
    except Exception as e:
        logger.error(f"Recipients API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/subscriptions', methods=['GET', 'POST', 'DELETE'])
def api_subscriptions():
    """Enhanced subscriptions management API."""
    try:
        if request.method == 'GET':
            email = request.args.get('email', '').strip()
            if email:
                products = subscriptions_store.get_products(email)
                return jsonify({'success': True, 'products': products})
            else:
                all_subs = subscriptions_store.list_all_subscriptions()
                return jsonify({'success': True, 'subscriptions': all_subs})
        
        elif request.method == 'POST':
            data = request.get_json()
            email = data.get('email', '').strip()
            url = data.get('url', '').strip()
            
            # Validate that we support this retailer
            retailer = registry.get_retailer_for_url(url)
            if not retailer:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported retailer for URL: {url}',
                    'supported_retailers': registry.get_supported_retailers()
                }), 400
            
            result = subscriptions_store.add_product(email, url)
            return jsonify(result), 200 if result['success'] else 400
        
        elif request.method == 'DELETE':
            data = request.get_json()
            email = data.get('email', '').strip()
            url = data.get('url', '').strip()
            
            result = subscriptions_store.remove_product(email, url)
            return jsonify(result), 200 if result['success'] else 404
            
    except Exception as e:
        logger.error(f"Subscriptions API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize with enhanced scraping
    try:
        logger.info("Initializing enhanced web app...")
        app_state.system_status = "initializing"
        
        # Perform initial enhanced scrape
        initial_results = main_enhanced.scrape_products_enhanced()
        app_state.update_scrape_results(initial_results)
        app_state.system_status = "healthy"
        
        logger.info(f"Enhanced web app initialized with {len(initial_results)} products")
        
    except Exception as e:
        logger.warning(f"Initial enhanced scrape failed: {e}")
        app_state.system_status = "degraded"
    
    # Start the enhanced web app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"Starting enhanced Sale Tracker web app on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Supported retailers: {registry.get_supported_retailers()}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)