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
import subscriptions_store

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
CRON_TOKEN = os.getenv('CRON_TOKEN')

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
    scheduler_text = "Scheduled via GitHub Actions" if CRON_TOKEN else None
    return render_template('dashboard.html', 
                         products=app_state.last_scrape_results,
                         is_running=app_state.is_running,
                         last_email=app_state.last_email_sent,
                         config=config,
                         scheduler_text=scheduler_text)

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
        # Prefer personalized emails if subscriptions exist; else fallback
        main_improved.send_personalized_emails()
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

@app.route('/api/cron/send', methods=['POST', 'GET'])
def api_cron_send():
    """Secure endpoint for external cron (e.g., GitHub Actions) to trigger daily emails."""
    try:
        provided = request.headers.get('X-CRON-TOKEN') or request.args.get('token') or ''
        if not CRON_TOKEN or provided != CRON_TOKEN:
            app.logger.warning(f"Unauthorized cron attempt from {request.remote_addr}")
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        app.logger.info("Cron-triggered daily email starting...")
        
        # Pre-flight checks
        try:
            sender_email, sender_password, recipient_emails = main_improved.get_email_credentials()
            if not recipient_emails:
                return jsonify({
                    'success': False, 
                    'error': 'No recipients configured',
                    'details': 'Add recipients via web interface or set RECIPIENT_EMAIL environment variable'
                }), 400
                
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': 'Email configuration error',
                'details': str(e)
            }), 400

        # Attempt to send emails
        main_improved.send_personalized_emails()
        app_state.last_email_sent = datetime.now().isoformat()
        
        app.logger.info(f"Daily emails sent successfully to {len(recipient_emails)} recipients")
        return jsonify({
            'success': True, 
            'timestamp': app_state.last_email_sent,
            'recipients_count': len(recipient_emails)
        })
        
    except Exception as e:
        app.logger.error(f"Cron email send failed: {e}")
        return jsonify({
            'success': False, 
            'error': 'Email sending failed',
            'details': str(e)
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

@app.route('/api/health')
def api_health():
    """Comprehensive health check endpoint for configuration validation."""
    health_status = {
        'overall_status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'issues': [],
        'configuration': {},
        'recommendations': []
    }
    
    # Check email configuration
    try:
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("EMAIL_PASSWORD")
        
        if sender_email and sender_password:
            health_status['checks']['email_credentials'] = 'configured'
            health_status['configuration']['sender_email'] = sender_email
        else:
            health_status['checks']['email_credentials'] = 'missing'
            health_status['issues'].append('Email credentials (SENDER_EMAIL, EMAIL_PASSWORD) not configured')
            health_status['recommendations'].append('Set SENDER_EMAIL and EMAIL_PASSWORD environment variables')
            health_status['overall_status'] = 'degraded'
            
    except Exception as e:
        health_status['checks']['email_credentials'] = 'error'
        health_status['issues'].append(f'Error checking email credentials: {str(e)}')
    
    # Check recipients configuration
    try:
        recipients = recipients_store.load_recipients()
        env_recipients = []
        
        # Check environment variable recipients as fallback
        if os.getenv("RECIPIENT_EMAIL"):
            env_recipients.append(os.getenv("RECIPIENT_EMAIL"))
        if os.getenv("RECIPIENT_EMAIL2"):
            env_recipients.append(os.getenv("RECIPIENT_EMAIL2"))
            
        total_recipients = len(recipients) + len(env_recipients)
        
        if total_recipients > 0:
            health_status['checks']['recipients'] = 'configured'
            health_status['configuration']['recipient_count'] = total_recipients
            health_status['configuration']['recipients_source'] = 'storage' if recipients else 'environment'
        else:
            health_status['checks']['recipients'] = 'missing'
            health_status['issues'].append('No email recipients configured')
            health_status['recommendations'].append('Add recipients via web interface or set RECIPIENT_EMAIL environment variable')
            health_status['overall_status'] = 'unhealthy'
            
    except Exception as e:
        health_status['checks']['recipients'] = 'error'
        health_status['issues'].append(f'Error checking recipients: {str(e)}')
    
    # Check GitHub Actions configuration
    cron_token = os.getenv('CRON_TOKEN')
    if cron_token:
        health_status['checks']['github_actions'] = 'configured'
        health_status['configuration']['cron_token_set'] = True
    else:
        health_status['checks']['github_actions'] = 'missing'
        health_status['issues'].append('CRON_TOKEN not configured - GitHub Actions cannot trigger emails')
        health_status['recommendations'].append('Set CRON_TOKEN environment variable and matching GitHub secret')
        
    # Check if we can access external sites for scraping
    try:
        import requests
        test_response = requests.get('https://httpbin.org/status/200', timeout=5)
        if test_response.status_code == 200:
            health_status['checks']['external_access'] = 'available'
        else:
            health_status['checks']['external_access'] = 'limited'
            health_status['issues'].append('Limited external network access - product scraping may fail')
    except Exception as e:
        health_status['checks']['external_access'] = 'unavailable'
        health_status['issues'].append(f'No external network access: {str(e)}')
        
    # Check Flask environment
    flask_env = os.getenv('FLASK_ENV', 'development')
    health_status['configuration']['flask_environment'] = flask_env
    
    if flask_env == 'production':
        health_status['checks']['environment'] = 'production'
    else:
        health_status['checks']['environment'] = 'development'
        health_status['recommendations'].append('Set FLASK_ENV=production for deployment')
    
    # Check log file accessibility
    try:
        with open('sale_tracker.log', 'a'):
            health_status['checks']['logging'] = 'available'
    except Exception as e:
        health_status['checks']['logging'] = 'limited'
        health_status['issues'].append(f'Cannot write to log file: {str(e)}')
    
    # Final status determination
    if health_status['issues']:
        if any('missing' in issue.lower() or 'no email recipients' in issue.lower() for issue in health_status['issues']):
            health_status['overall_status'] = 'unhealthy'
        else:
            health_status['overall_status'] = 'degraded'
    
    status_code = 200 if health_status['overall_status'] == 'healthy' else 503
    return jsonify(health_status), status_code


@app.route('/api/test-email', methods=['POST'])
def api_test_email():
    """Test endpoint to verify email configuration without sending to all recipients."""
    try:
        data = request.get_json() or {}
        test_email = data.get('email')
        
        if not test_email:
            return jsonify({
                'success': False,
                'error': 'Email address required',
                'details': 'Provide email address in request body: {"email": "test@example.com"}'
            }), 400
        
        # Validate email configuration
        try:
            sender_email, sender_password, _ = main_improved.get_email_credentials()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': 'Email configuration error',
                'details': str(e)
            }), 400
        
        # Send test email
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = test_email
        message['Subject'] = f'Sale Tracker Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        
        body = f"""
        This is a test email from your Sale Tracker application.
        
        Configuration Test Results:
        - Sender Email: {sender_email}
        - Timestamp: {datetime.now().isoformat()}
        - Server: {request.host}
        
        If you received this email, your email configuration is working correctly!
        
        Next steps:
        1. Add product URLs via the web interface
        2. The system will send daily updates at 21:00 UTC
        3. GitHub Actions will trigger the daily emails automatically
        """
        
        message.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(main_improved.config.EMAIL_SETTINGS["smtp_server"], 
                             main_improved.config.EMAIL_SETTINGS["smtp_port"])
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, test_email, message.as_string())
        server.quit()
        
        app.logger.info(f"Test email sent successfully to {test_email}")
        return jsonify({
            'success': True,
            'message': 'Test email sent successfully',
            'recipient': test_email,
            'timestamp': datetime.now().isoformat()
        })
        
    except smtplib.SMTPAuthenticationError as e:
        app.logger.error(f"SMTP Authentication Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Email authentication failed',
            'details': 'Check SENDER_EMAIL and EMAIL_PASSWORD. For Gmail, use App Password not regular password.'
        }), 400
        
    except smtplib.SMTPException as e:
        app.logger.error(f"SMTP Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Email server error',
            'details': str(e)
        }), 500
        
    except Exception as e:
        app.logger.error(f"Test email failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Email test failed',
            'details': str(e)
        }), 500


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


@app.route('/api/subscriptions', methods=['GET', 'POST', 'DELETE'])
def api_subscriptions():
    try:
        if request.method == 'GET':
            email = (request.args.get('email') or '').strip().lower()
            if email:
                return jsonify({'success': True, 'products': subscriptions_store.get_products(email)})
            return jsonify({'success': True, 'all': subscriptions_store.list_all_subscriptions()})

        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        url = (data.get('url') or '').strip()

        if request.method == 'POST':
            result = subscriptions_store.add_product(email, url)
            status = 200 if result.get('success') else 400
            return jsonify(result), status

        if request.method == 'DELETE':
            result = subscriptions_store.remove_product(email, url)
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
