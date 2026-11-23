import json
import logging
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

import requests
import schedule
from bs4 import BeautifulSoup
from dotenv import load_dotenv

import config
import recipients_store
import scraper
import subscriptions_store

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('sale_tracker.log'), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def get_email_credentials() -> Tuple[str, str, List[str]]:
    """Get email credentials from environment variables with fallbacks."""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")

    # Determine recipients from recipients_store first; fall back to env vars
    dynamic_recipients = recipients_store.load_recipients()
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    recipient_email2 = os.getenv("RECIPIENT_EMAIL2")

    if not sender_email or not sender_password:
        raise ValueError("SENDER_EMAIL and EMAIL_PASSWORD must be set in .env file")

    # Build recipient list with precedence: dynamic store > env vars
    recipient_emails: List[str] = []
    if dynamic_recipients:
        recipient_emails = dynamic_recipients
    else:
        if not recipient_email:
            raise ValueError("No recipients configured. Add via web UI or set RECIPIENT_EMAIL in .env")
        recipient_emails = [recipient_email]
        if recipient_email2:
            recipient_emails.append(recipient_email2)

    return sender_email, sender_password, recipient_emails


def _scrape(product_link: str) -> Tuple[str, str, str]:
    """Scrape any supported product URL and return (name, price, image)."""
    result = scraper.scrape(product_link, force=True)
    name = result.get("name") or "Product name not found"
    price = result.get("price_display") or "Price not found"
    image = result.get("image") or ""
    if not result.get("success"):
        logger.warning("Could not read a price for %s: %s", product_link, result.get("error"))
    return name, price, image


def scrape_lululemon(product_link: str) -> Tuple[str, str, str]:
    """Scrape product information from a Lululemon URL."""
    return _scrape(product_link)


def scrape_nike(product_link: str) -> Tuple[str, str, str]:
    """Scrape product information from a Nike URL."""
    return _scrape(product_link)


def _collect_products(entries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Scrape each entry and attach the retailer key used by the email."""
    products = []
    for entry in entries:
        url = entry.get("url")
        if not url:
            continue
        result = scraper.scrape(url, force=True)
        result["company"] = entry.get("company") or result.get("retailer", "")
        products.append(result)
    return products


def _build_email(sender_email: str, recipients: List[str], products: List[Dict[str, Any]]):
    """Build the daily digest message."""
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)

    prices = [p["price_display"] for p in products if p.get("price_display")]
    subject_prices = ", ".join(prices) if prices else "Your tracked products"
    message["Subject"] = f"{subject_prices} - Your Tracked Products ({datetime.now().strftime('%Y-%m-%d')})"

    cards = []
    for product in products:
        name = product.get("name") or "Product"
        image = product.get("image") or ""
        price = product.get("price_display")
        if price:
            price_html = f'<p style="font-size: 20px; font-weight: bold; color: #0b3558; margin: 10px 0;">{price}</p>'
        else:
            reason = "The store blocked the price check" if product.get("status") == "blocked" else "No price found"
            price_html = f'<p style="font-size: 14px; color: #476788; margin: 10px 0;">{reason}</p>'

        cards.append(f"""
        <div style="width: 100%; text-align: center;">
            <div style="display: inline-block; border: 1px solid #d4e0ed; padding: 20px; margin-bottom: 20px; max-width: 400px; border-radius: 16px;">
                <a href="{product['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                    <h3 style="margin: 0 0 10px 0; color: #0b3558;">{name}</h3>
                    {price_html}
                    <p style="font-size: 12px; color: #476788; margin: 5px 0; text-transform: uppercase;">{product.get('company', '')}</p>
                    {f'<img src="{image}" alt="{name}" style="width: 80%; max-width: 300px; height: auto; border-radius: 8px;" />' if image else ''}
                </a>
            </div>
        </div>
        """)

    html_body = "\n".join(
        [
            "<html><body>",
            f"<h2>Your tracked products for {datetime.now().strftime('%B %d, %Y')}:</h2>",
            *cards,
            "</body></html>",
        ]
    )
    message.attach(MIMEText(html_body, "html"))
    return message


def _send_message(message, sender_email: str, sender_password: str, recipients: List[str]) -> None:
    server = smtplib.SMTP(config.EMAIL_SETTINGS["smtp_server"], config.EMAIL_SETTINGS["smtp_port"])
    server.starttls()
    server.login(sender_email, sender_password)
    for recipient in recipients:
        server.sendmail(sender_email, recipient, message.as_string())
        logger.info(f"Email sent successfully to {recipient}")
    server.quit()


def send_combined_email() -> None:
    """Send one email with every product from config.py."""
    try:
        sender_email, sender_password, recipient_emails = get_email_credentials()
        entries = [{"company": company, "url": link} for company, links in config.PRODUCT_LINKS.items() for link in links]
        products = _collect_products(entries)
        if not products:
            logger.error("No products were scraped")
            return
        message = _build_email(sender_email, recipient_emails, products)
        _send_message(message, sender_email, sender_password, recipient_emails)
        logger.info("Combined email sent successfully")
    except Exception as exc:
        logger.error(f"Failed to send combined email: {exc}")


def send_personalized_emails() -> None:
    """Send each recipient a digest of the products they follow."""
    try:
        sender_email, sender_password, recipient_emails = get_email_credentials()
        all_subs = subscriptions_store.list_all_subscriptions()

        for recipient in sorted(set(email.lower() for email in recipient_emails)):
            entries = all_subs.get(recipient, [])
            if not entries:
                logger.info(f"No personalized products for {recipient}, using global config list")
                entries = [
                    {"company": company, "url": link} for company, links in config.PRODUCT_LINKS.items() for link in links
                ]

            products = _collect_products(entries)
            if not products:
                logger.info(f"No products to email for {recipient}")
                continue

            message = _build_email(sender_email, [recipient], products)
            _send_message(message, sender_email, sender_password, [recipient])
            logger.info(f"Personalized email sent to {recipient}")
    except Exception as exc:
        logger.error(f"Failed to send personalized emails: {exc}")


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):  # Bundled with py2app
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def run_scheduler() -> None:
    """Run the scheduler to send emails at the specified time."""
    logger.info("Starting Sale Tracker scheduler")
    logger.info(f"Emails will be sent daily at {config.EMAIL_SETTINGS['schedule_time']}")

    # Use personalized emails when available
    schedule.every().day.at(config.EMAIL_SETTINGS["schedule_time"]).do(send_personalized_emails)

    # Send immediately for testing (uncomment the next line to test)
    # send_combined_email()

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute instead of every second
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)  # Wait before retrying


if __name__ == '__main__':
    try:
        run_scheduler()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)
