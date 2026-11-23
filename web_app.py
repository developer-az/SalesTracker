#!/usr/bin/env python3
"""
Sale Tracker Web Application
Flask API + dashboard for tracked product prices.
"""

import os
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template, request

import config
import main_improved
import recipients_store
import scraper
import subscriptions_store

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
CRON_TOKEN = os.getenv('CRON_TOKEN')


class WebAppState:
    def __init__(self):
        self.last_scrape_results = []
        self.is_running = False
        self.last_email_sent = None
        self.scheduler_thread = None

    def update_scrape_results(self, results):
        self.last_scrape_results = results


app_state = WebAppState()


def _products_for_email(email, force=False):
    """Return tracked products for an email with live price data."""
    subscriptions = subscriptions_store.get_products(email)
    if not subscriptions:
        return []

    urls = [entry.get("url") for entry in subscriptions if entry.get("url")]
    scraped = scraper.scrape_many(urls, force=force)
    by_url = {item["url"]: item for item in scraped}

    products = []
    for entry in subscriptions:
        url = entry.get("url")
        item = dict(by_url.get(url) or {})
        item.setdefault("url", url)
        item.setdefault("retailer", (entry.get("company") or "").title())
        item["company"] = entry.get("company")
        item["added_at"] = entry.get("added_at")
        products.append(item)
    return products


@app.route('/')
def index():
    scheduler_text = "Scheduled via GitHub Actions" if CRON_TOKEN else None
    return render_template(
        'dashboard.html',
        products=[],
        is_running=app_state.is_running,
        last_email=app_state.last_email_sent,
        config=config,
        scheduler_text=scheduler_text,
    )


@app.route('/api/products')
def api_products():
    """Tracked products for one email, with freshly scraped prices."""
    email = (request.args.get('email') or '').strip().lower()
    if not email:
        return jsonify({'success': True, 'products': [], 'timestamp': datetime.now().isoformat()})
    try:
        products = _products_for_email(email)
        app_state.update_scrape_results(products)
        return jsonify(
            {
                'success': True,
                'products': products,
                'timestamp': datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        app.logger.exception("Failed to load products")
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/products/refresh', methods=['POST'])
def api_products_refresh():
    """Re-scrape the tracked products for one email (or a single URL)."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    url = (data.get('url') or '').strip()

    if not email and not url:
        return jsonify({'success': False, 'error': 'Email or URL is required'}), 400

    try:
        if url and not email:
            product = scraper.scrape(url, force=True)
            return jsonify({'success': True, 'product': product})
        products = _products_for_email(email, force=True)
        app_state.update_scrape_results(products)
        return jsonify(
            {
                'success': True,
                'products': products,
                'timestamp': datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        app.logger.exception("Failed to refresh products")
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/scrape')
def api_scrape():
    """Legacy endpoint: scrape the products in config.py."""
    try:
        urls = [link for links in config.PRODUCT_LINKS.values() for link in links]
        results = scraper.scrape_many(urls)
        for item in results:
            item['company'] = item['retailer'].lower()
            item['link'] = item['url']
            item['timestamp'] = item.get('fetched_at')
        app_state.update_scrape_results(results)
        return jsonify(
            {
                'success': True,
                'products': results,
                'timestamp': datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/send-test-email')
def api_send_test_email():
    """Send the daily digest right now."""
    try:
        main_improved.send_personalized_emails()
        app_state.last_email_sent = datetime.now().isoformat()
        return jsonify(
            {
                'success': True,
                'message': 'Email sent',
                'timestamp': app_state.last_email_sent,
            }
        )
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/cron/send', methods=['POST', 'GET'])
def api_cron_send():
    """Secure endpoint for external cron (e.g. GitHub Actions)."""
    try:
        provided = request.headers.get('X-CRON-TOKEN') or request.args.get('token') or ''
        if not CRON_TOKEN or provided != CRON_TOKEN:
            app.logger.warning(f"Unauthorized cron attempt from {request.remote_addr}")
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        app.logger.info("Cron-triggered daily email starting...")

        try:
            sender_email, sender_password, recipient_emails = main_improved.get_email_credentials()
            if not recipient_emails:
                return (
                    jsonify(
                        {
                            'success': False,
                            'error': 'No recipients configured',
                            'details': 'Add recipients via the web interface or set RECIPIENT_EMAIL',
                        }
                    ),
                    400,
                )
        except ValueError as exc:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Email configuration error',
                        'details': str(exc),
                    }
                ),
                400,
            )

        main_improved.send_personalized_emails()
        app_state.last_email_sent = datetime.now().isoformat()

        app.logger.info(f"Daily emails sent successfully to {len(recipient_emails)} recipients")
        return jsonify(
            {
                'success': True,
                'timestamp': app_state.last_email_sent,
                'recipients_count': len(recipient_emails),
            }
        )
    except Exception as exc:
        app.logger.error(f"Cron email send failed: {exc}")
        return (
            jsonify(
                {
                    'success': False,
                    'error': 'Email sending failed',
                    'details': str(exc),
                }
            ),
            500,
        )


@app.route('/api/start-scheduler')
def api_start_scheduler():
    try:
        if not app_state.is_running:

            def run_scheduler():
                app_state.is_running = True
                try:
                    main_improved.run_scheduler()
                except Exception:
                    pass
                finally:
                    app_state.is_running = False

            app_state.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            app_state.scheduler_thread.start()

        return jsonify(
            {
                'success': True,
                'message': 'Scheduler started',
                'is_running': app_state.is_running,
            }
        )
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/stop-scheduler')
def api_stop_scheduler():
    try:
        app_state.is_running = False
        return jsonify(
            {
                'success': True,
                'message': 'Scheduler stop requested',
                'is_running': app_state.is_running,
            }
        )
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/config')
def api_config():
    return jsonify(
        {
            'product_links': config.PRODUCT_LINKS,
            'email_settings': config.EMAIL_SETTINGS,
            'scraping_settings': config.SCRAPING_SETTINGS,
            'recipients': recipients_store.load_recipients(),
            'supported_retailers': ['Lululemon', 'Nike', 'any retailer with structured product data'],
        }
    )


@app.route('/api/status')
def api_status():
    return jsonify(
        {
            'is_running': app_state.is_running,
            'last_email_sent': app_state.last_email_sent,
            'products_count': len(app_state.last_scrape_results),
            'last_scrape': (app_state.last_scrape_results[-1].get('fetched_at') if app_state.last_scrape_results else None),
        }
    )


@app.route('/api/health')
def api_health():
    """Health check for deployment monitors."""
    health = {
        'overall_status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'issues': [],
        'configuration': {},
        'recommendations': [],
    }

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")
    if sender_email and sender_password:
        health['checks']['email_credentials'] = 'configured'
        health['configuration']['sender_email'] = sender_email
    else:
        health['checks']['email_credentials'] = 'missing'
        health['issues'].append('Email credentials (SENDER_EMAIL, EMAIL_PASSWORD) not configured')
        health['recommendations'].append('Set SENDER_EMAIL and EMAIL_PASSWORD environment variables')
        health['overall_status'] = 'degraded'

    try:
        recipients = recipients_store.load_recipients()
        env_recipients = [v for v in (os.getenv("RECIPIENT_EMAIL"), os.getenv("RECIPIENT_EMAIL2")) if v]
        total = len(recipients) + len(env_recipients)
        if total:
            health['checks']['recipients'] = 'configured'
            health['configuration']['recipient_count'] = total
            health['configuration']['recipients_source'] = 'storage' if recipients else 'environment'
        else:
            health['checks']['recipients'] = 'missing'
            health['issues'].append('No email recipients configured')
            health['recommendations'].append('Add recipients via the web interface or set RECIPIENT_EMAIL')
            health['overall_status'] = 'unhealthy'
    except Exception as exc:
        health['checks']['recipients'] = 'error'
        health['issues'].append(f'Error checking recipients: {exc}')

    if os.getenv('CRON_TOKEN'):
        health['checks']['github_actions'] = 'configured'
        health['configuration']['cron_token_set'] = True
    else:
        health['checks']['github_actions'] = 'missing'
        health['issues'].append('CRON_TOKEN not configured - GitHub Actions cannot trigger emails')
        health['recommendations'].append('Set CRON_TOKEN and a matching GitHub secret')

    health['checks']['scraper'] = 'ready'
    health['configuration']['browser_client'] = 'available' if scraper.cffi_requests else 'requests only'

    flask_env = os.getenv('FLASK_ENV', 'development')
    health['configuration']['flask_environment'] = flask_env
    health['checks']['environment'] = 'production' if flask_env == 'production' else 'development'

    try:
        with open('sale_tracker.log', 'a'):
            health['checks']['logging'] = 'available'
    except Exception:
        health['checks']['logging'] = 'limited'

    if health['issues'] and health['overall_status'] == 'healthy':
        health['overall_status'] = 'degraded'

    status_code = 200 if health['overall_status'] == 'healthy' else 503
    return jsonify(health), status_code


@app.route('/api/test-email', methods=['POST'])
def api_test_email():
    """Send a test email without touching the whole digest."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        data = request.get_json() or {}
        test_email = (data.get('email') or '').strip()

        if not recipients_store.validate_email(test_email):
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'A valid email address is required',
                        'details': 'Send {"email": "test@example.com"}',
                    }
                ),
                400,
            )

        try:
            sender_email, sender_password, _ = main_improved.get_email_credentials()
        except ValueError as exc:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Email configuration error',
                        'details': str(exc),
                    }
                ),
                400,
            )

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = test_email
        message['Subject'] = f'Sale Tracker test email - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        message.attach(
            MIMEText(
                "This is a test email from Sale Tracker.\n\n"
                f"Sender: {sender_email}\nTimestamp: {datetime.now().isoformat()}\n\n"
                "If you received this, your email configuration works.",
                'plain',
            )
        )

        server = smtplib.SMTP(
            main_improved.config.EMAIL_SETTINGS["smtp_server"],
            main_improved.config.EMAIL_SETTINGS["smtp_port"],
        )
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, test_email, message.as_string())
        server.quit()

        return jsonify(
            {
                'success': True,
                'message': 'Test email sent',
                'recipient': test_email,
                'timestamp': datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        app.logger.error(f"Test email failed: {exc}")
        return (
            jsonify(
                {
                    'success': False,
                    'error': 'Email test failed',
                    'details': str(exc),
                }
            ),
            500,
        )


@app.route('/api/recipients', methods=['GET', 'POST', 'DELETE'])
def api_recipients():
    try:
        if request.method == 'GET':
            return jsonify(
                {
                    'success': True,
                    'recipients': recipients_store.load_recipients(),
                }
            )

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
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


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
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
