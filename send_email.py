import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import schedule
import time
import requests
from bs4 import BeautifulSoup
import json

load_dotenv()  # Load EMAIL credentials from .env file

# Load credentials from environment
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("EMAIL_PASSWORD")
recipient_emails = [os.getenv("RECIPIENT_EMAIL"),os.getenv("RECIPIENT_EMAIL2")] 

lululemon_link_1 = "https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786?color=0001"
lululemon_link_2 = "https://shop.lululemon.com/p/mens-jackets-and-outerwear/Pace-Breaker-Jacket/_/prod11670131?cid=Google_SHOP_US_NAT_EN_X_BrandShop_Incr-All_OMNI_GEN_Y24_ag-SHOP_G_US_EN_DM_M_GEN_NO_Tops-Jackets&color=0001&gad_campaignid=21471260535&gad_source=1&gbraid=0AAAAADL8Avk5CDt35HKBgpfRSuD0CpJvP&gclid=CjwKCAjwkbzEBhAVEiwA4V-yqpMcLNT4qAeAlXO9G-dH0QPZKbelVx2jrlqZrfrChowBqSPFpaclcxoCx5oQAvD_BwE&gclsrc=aw.ds&locale=en_US&sl=US&sz=S"
nike_link = "https://www.nike.com/t/unlimited-mens-repel-hooded-versatile-jacket-56pDjs/FB7551-010"
links = {}
links["lululemon"] = [lululemon_link_1, lululemon_link_2]
links["nike"] = [nike_link]


def scrape_lululemon(product_link):
    
    response = requests.get(product_link)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    name_element = soup.find("meta", attrs={'property': 'og:title'})
    price_element = soup.find('span', class_='price') 

    name = name_element.get("content") if name_element else "Product name not found"
    price = price_element.get_text(strip=True) if price_element else "Price not found"

    return name, price

def scrape_nike(product_link):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(product_link, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find and parse the JSON-LD product data
    json_ld = soup.find("script", type="application/ld+json")
    data = json.loads(json_ld.string)

    # Extract name and price
    name = data.get("name") if data else "Product name not found"
    price = "$" + str(data.get("offers", {}).get("lowPrice")) + "USD" if data and "offers" in data else "Price not found"

    return name, price

def send_email(product_link, company):
    # Get product details
    if company == "lululemon":
        product_name, product_price = scrape_lululemon(product_link)
    elif company == "nike":
        product_name, product_price = scrape_nike(product_link)

    # Create the email
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = ", ".join(recipient_emails)
    message['Subject'] = f"{product_price}! Your Product {product_name} is on sale!"
    body = f"The price of {product_name} is: {product_price}, \nCheck it out here: {product_link}"
    message.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        for recipient in recipient_emails:
            server.sendmail(sender_email, recipient, message.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)

def send_combined_email():
    all_products_info = []
    prices_for_subject = []

    for company in links:
        for link in links[company]:
            if company == "lululemon":
                name, price = scrape_lululemon(link)
            elif company == "nike":
                name, price = scrape_nike(link)
            all_products_info.append((name, price, link))
            prices_for_subject.append(price.replace("USD", "").strip())

    # Build email body
    body_lines = ["Here are your tracked products:\n"]
    for name, price, link in all_products_info:
        body_lines.append(f"{name} — {price}\n{link}\n")

    body = "\n".join(body_lines)

    # Compose email
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = ", ".join(recipient_emails)

    subject_prices = f"{prices_for_subject[0]}/228, {prices_for_subject[1]}/168, {prices_for_subject[2]}/110" 
    message['Subject'] = f"{subject_prices} – Your Tracked Products"

    message.attach(MIMEText(body, 'plain'))

    # Send email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        for recipient in recipient_emails:
            server.sendmail(sender_email, recipient, message.as_string())
        server.quit()
        print("Combined email sent successfully.")
    except Exception as e:
        print("Failed to send combined email:", e)

# Run
# for company in links:
#     for link in links[company]:
#         schedule.every().day.at("21:00").do(send_email, link, company)  # Schedule to run daily at 9 PM
#         send_email(link, company)

schedule.every().day.at("21:00").do(send_combined_email)
send_combined_email()  # Send immediately for testing

while True:
    schedule.run_pending()
    try:
        time.sleep(1)  # Sleep to prevent busy waiting
    except KeyboardInterrupt:
        print("Scheduler stopped.")
        break
