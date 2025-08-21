#!/usr/bin/env python3
"""
Sale Tracker Web Application
Modern Flask web interface for the Sale Tracker
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import os
import json
from datetime import datetime
import threading
import time

# Import our improved modules
import main_improved
import config
import recipients_store

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Global state for tracking
class WebAppState:
    def __init__(self):
        self.last_scrape_results = []
        self.is_running = False
        self.last_email_sent = None
        self.scheduler_thread = None
        
    def update_scrape_results(self, results):
        self.last_scrape_results = results
        
app_state = WebAppState()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html', 
                         products=app_state.last_scrape_results,
                         is_running=app_state.is_running,
                         last_email=app_state.last_email_sent,
                         config=config)

@app.route('/api/scrape')
def api_scrape():
    """API endpoint to scrape all products."""
    try:
        results = []
        
        for company, links in config.PRODUCT_LINKS.items():
            for link in links:
                try:
                    if company == "lululemon":
                        name, price, image = main_improved.scrape_lululemon(link)
                    elif company == "nike":
                        name, price, image = main_improved.scrape_nike(link)
                    else:
                        continue
                    
                    results.append({
                        'company': company,
                        'name': name,
                        'price': price,
                        'image': image,
                        'link': link,
                        'timestamp': datetime.now().isoformat(),
                        'success': name != "Product name not found"
                    })
                except Exception as e:
                    results.append({
                        'company': company,
                        'name': f"Error: {str(e)}",
                        'price': "N/A",
                        'image': "",
                        'link': link,
                        'timestamp': datetime.now().isoformat(),
                        'success': False
                    })
        
        app_state.update_scrape_results(results)
        return jsonify({
            'success': True,
            'products': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/send-test-email')
def api_send_test_email():
    """API endpoint to send a test email."""
    try:
        main_improved.send_combined_email()
        app_state.last_email_sent = datetime.now().isoformat()
        return jsonify({
            'success': True,
            'message': 'Test email sent successfully',
            'timestamp': app_state.last_email_sent
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/start-scheduler')
def api_start_scheduler():
    """API endpoint to start the scheduler."""
    try:
        if not app_state.is_running:
            def run_scheduler():
                app_state.is_running = True
                try:
                    main_improved.run_scheduler()
                except:
                    pass
                finally:
                    app_state.is_running = False
            
            app_state.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            app_state.scheduler_thread.start()
            
        return jsonify({
            'success': True,
            'message': 'Scheduler started',
            'is_running': app_state.is_running
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stop-scheduler')
def api_stop_scheduler():
    """API endpoint to stop the scheduler."""
    try:
        app_state.is_running = False
        return jsonify({
            'success': True,
            'message': 'Scheduler stop requested',
            'is_running': app_state.is_running
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def api_config():
    """API endpoint to get current configuration."""
    return jsonify({
        'product_links': config.PRODUCT_LINKS,
        'email_settings': config.EMAIL_SETTINGS,
        'scraping_settings': config.SCRAPING_SETTINGS,
        'recipients': recipients_store.load_recipients()
    })

@app.route('/api/status')
def api_status():
    """API endpoint to get application status."""
    return jsonify({
        'is_running': app_state.is_running,
        'last_email_sent': app_state.last_email_sent,
        'products_count': len(app_state.last_scrape_results),
        'last_scrape': app_state.last_scrape_results[-1]['timestamp'] if app_state.last_scrape_results else None
    })


@app.route('/api/recipients', methods=['GET', 'POST', 'DELETE'])
def api_recipients():
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'recipients': recipients_store.load_recipients()
            })

        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip()

        if request.method == 'POST':
            result = recipients_store.add_recipient(email)
            status = 200 if result.get('success') else 400
            return jsonify(result), status

        if request.method == 'DELETE':
            result = recipients_store.remove_recipient(email)
            status = 200 if result.get('success') else 404
            return jsonify(result), status

        return jsonify({'success': False, 'error': 'Unsupported method'}), 405
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize with a scrape
    try:
        import requests
        # Quick test to see if we can scrape
        app.logger.info("Initializing with initial scrape...")
        with app.app_context():
            api_scrape()
    except:
        app.logger.warning("Initial scrape failed, continuing anyway...")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
