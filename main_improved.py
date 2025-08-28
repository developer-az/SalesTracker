import json
import logging
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Tuple

import requests
import schedule
from bs4 import BeautifulSoup
from dotenv import load_dotenv

import config
import recipients_store
import subscriptions_store

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("sale_tracker.log"), logging.StreamHandler()],
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


def scrape_lululemon(product_link: str) -> Tuple[str, str, str]:
    """Scrape product information from Lululemon with error handling."""
    try:
        headers = {"User-Agent": config.SCRAPING_SETTINGS["user_agent"]}
        response = requests.get(product_link, headers=headers, timeout=config.SCRAPING_SETTINGS["timeout"])
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        name_element = soup.find("meta", attrs={"property": "og:title"})
        price_element = soup.find("span", class_="price")
        image_element = soup.find("meta", property="og:image")

        name = name_element.get("content") if name_element else "Product name not found"
        price = price_element.get_text(strip=True) if price_element else "Price not found"
        image = image_element["content"] if image_element else ""

        logger.info(f"Successfully scraped Lululemon product: {name} - {price}")
        return name, price, image

    except requests.RequestException as e:
        logger.error(f"Failed to scrape Lululemon product: {e}")
        return "Product name not found", "Price not found", ""
    except Exception as e:
        logger.error(f"Unexpected error scraping Lululemon product: {e}")
        return "Product name not found", "Price not found", ""


def scrape_nike(product_link: str) -> Tuple[str, str, str]:
    """Scrape product information from Nike with error handling."""
    try:
        headers = {"User-Agent": config.SCRAPING_SETTINGS["user_agent"]}
        response = requests.get(product_link, headers=headers, timeout=config.SCRAPING_SETTINGS["timeout"])
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find and parse the JSON-LD product data
        json_ld = soup.find("script", type="application/ld+json")
        if not json_ld:
            logger.warning("No JSON-LD data found for Nike product")
            return "Product name not found", "Price not found", ""

        data = json.loads(json_ld.string)
        image_element = soup.find("meta", property="og:image")

        # Extract name and price
        name = data.get("name", "Product name not found")
        price_data = data.get("offers", {})
        price = f"${price_data.get('lowPrice', 'N/A')}USD" if price_data else "Price not found"
        image = image_element["content"] if image_element else ""

        logger.info(f"Successfully scraped Nike product: {name} - {price}")
        return name, price, image

    except requests.RequestException as e:
        logger.error(f"Failed to scrape Nike product: {e}")
        return "Product name not found", "Price not found", ""
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON-LD data for Nike product: {e}")
        return "Product name not found", "Price not found", ""
    except Exception as e:
        logger.error(f"Unexpected error scraping Nike product: {e}")
        return "Product name not found", "Price not found", ""


def send_combined_email() -> None:
    """Send combined email with all product information (global list)."""
    try:
        sender_email, sender_password, recipient_emails = get_email_credentials()

        all_products_info = []
        prices_for_subject = []

        # Scrape all products
        for company, links in config.PRODUCT_LINKS.items():
            for link in links:
                if company == "lululemon":
                    name, price, image = scrape_lululemon(link)
                elif company == "nike":
                    name, price, image = scrape_nike(link)
                else:
                    logger.warning(f"Unknown company: {company}")
                    continue

                all_products_info.append((name, price, image, link, company))
                # Clean price for subject line
                clean_price = price.replace("USD", "").replace("$", "").strip()
                prices_for_subject.append(clean_price)

        if not all_products_info:
            logger.error("No products were successfully scraped")
            return

        # Compose email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = ", ".join(recipient_emails)

        # Create dynamic subject line
        subject_prices = ", ".join(prices_for_subject)
        message["Subject"] = f"{subject_prices} – Your Tracked Products ({datetime.now().strftime('%Y-%m-%d')})"

        # Build email body
        html_lines = ["<html><body>", f"<h2>Here are your tracked products for {datetime.now().strftime('%B %d, %Y')}:</h2>"]

        for name, price, image, link, company in all_products_info:
            card = f"""
            <div style="width: 100%; text-align: center;">
                <div style="
                    display: inline-block;
                    border: 1px solid #ccc;
                    padding: 20px;
                    margin-bottom: 20px;
                    max-width: 400px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">{name}</h3>
                        <p style="font-size: 18px; font-weight: bold; color: #e74c3c; margin: 10px 0;">{price}</p>
                        <p style="font-size: 12px; color: #666; margin: 5px 0;">{company.upper()}</p>
                        {f'<img src="{image}" alt="{name}" style="width: 80%; max-width: 300px; height: auto; border-radius: 4px;" />' if image else ''}
                    </a>
                </div>
            </div>
            """
            html_lines.append(card)

        html_lines.append("</body></html>")
        html_body = "\n".join(html_lines)
        message.attach(MIMEText(html_body, "html"))

        # Send email
        server = smtplib.SMTP(config.EMAIL_SETTINGS["smtp_server"], config.EMAIL_SETTINGS["smtp_port"])
        server.starttls()
        server.login(sender_email, sender_password)

        for recipient in recipient_emails:
            server.sendmail(sender_email, recipient, message.as_string())
            logger.info(f"Email sent successfully to {recipient}")

        server.quit()
        logger.info("Combined email sent successfully to all recipients")

    except Exception as e:
        logger.error(f"Failed to send combined email: {e}")


def send_personalized_emails() -> None:
    """Send personalized emails per recipient based on their subscriptions."""
    try:
        sender_email, sender_password, recipient_emails = get_email_credentials()
        all_subs = subscriptions_store.list_all_subscriptions()

        server = smtplib.SMTP(config.EMAIL_SETTINGS["smtp_server"], config.EMAIL_SETTINGS["smtp_port"])
        server.starttls()
        server.login(sender_email, sender_password)

        for recipient in set(recipient_emails):
            products = all_subs.get(recipient.lower(), [])
            # Fallback to global products if user has none
            if not products:
                logger.info(f"No personalized products for {recipient}, using global config list")
                per_user_links = []
                for company, links in config.PRODUCT_LINKS.items():
                    for link in links:
                        per_user_links.append({"company": company, "url": link})
            else:
                per_user_links = products

            collected = []
            subject_prices: List[str] = []
            for entry in per_user_links:
                company = entry.get("company")
                link = entry.get("url")
                if company == "lululemon":
                    name, price, image = scrape_lululemon(link)
                elif company == "nike":
                    name, price, image = scrape_nike(link)
                else:
                    continue
                collected.append((name, price, image, link, company))
                subject_prices.append(price.replace("USD", "").replace("$", "").strip())

            if not collected:
                logger.info(f"No products to email for {recipient}")
                continue

            # Compose email
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient
            subject_prices_str = ", ".join(subject_prices)
            message["Subject"] = f"{subject_prices_str} – Your Tracked Products ({datetime.now().strftime('%Y-%m-%d')})"

            html_lines = ["<html><body>", f"<h2>Your tracked products for {datetime.now().strftime('%B %d, %Y')}:</h2>"]
            for name, price, image, link, company in collected:
                card = f"""
                <div style=\"width: 100%; text-align: center;\">
                    <div style=\"
                        display: inline-block;
                        border: 1px solid #ccc;
                        padding: 20px;
                        margin-bottom: 20px;
                        max-width: 400px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    \">
                        <a href=\"{link}\" target=\"_blank\" style=\"text-decoration: none; color: inherit;\">
                            <h3 style=\"margin: 0 0 10px 0; color: #333;\">{name}</h3>
                            <p style=\"font-size: 18px; font-weight: bold; color: #e74c3c; margin: 10px 0;\">{price}</p>
                            <p style=\"font-size: 12px; color: #666; margin: 5px 0;\">{company.upper()}</p>
                            {f'<img src="{image}" alt="{name}" style="width: 80%; max-width: 300px; height: auto; border-radius: 4px;" />' if image else ''}
                        </a>
                    </div>
                </div>
                """
                html_lines.append(card)
            html_lines.append("</body></html>")
            message.attach(MIMEText("\n".join(html_lines), "html"))

            server.sendmail(sender_email, recipient, message.as_string())
            logger.info(f"Personalized email sent to {recipient}")

        server.quit()
    except Exception as e:
        logger.error(f"Failed to send personalized emails: {e}")


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, "frozen", False):  # Bundled with py2app
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


if __name__ == "__main__":
    try:
        run_scheduler()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)
