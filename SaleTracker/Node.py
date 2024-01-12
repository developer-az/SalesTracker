from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import os
import requests
from bs4 import BeautifulSoup

os.environ['REQUESTS_CA_BUNDLE'] = '/private/etc/ssl/cert.pem'
print("1")

app = Flask(__name__)
CORS(app)
print("2")

# Initialize the scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()
print("3")

# Example URL of the product
product_url = 'https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786?color=0001'  # Replace with the actual product URL

# Define a dictionary to store product details
product_details = {}

# Function to get product details
def get_product_details():
    print("get product details is running")
    try:
        # Send a GET request to the URL
        response = requests.get(product_url)
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Identify the HTML elements containing the name and price information
        # These will vary depending on the structure of the website
        # name_element = soup.find('h1', class_='product-title')  # Update with the correct tag and class
        name_element = soup.find('h1', class_='product-title_title__i8NUw').find('div')  # Update with the correct tag and class
        price_element = soup.find('span', class_='price')  # Update with the correct tag and class
        
        product_name = name_element.get_text().strip() if name_element else 'Product name not found'
        product_price = price_element.get_text().strip() if price_element else 'Price not found'
    
        return product_name, product_price
    except Exception as e:
        return f'Error: {str(e)}'
    

# Function to send daily email
def send_daily_email(email):
    print("send daily email is running")
    sender_email = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')

    if not product_details:
        # Fetch product details only if not already fetched
        product_details['name'], product_details['price'] = get_product_details()

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = email
    message['Subject'] = 'Your Daily Email Subject'

    body = f'The price of {product_details["name"]} is: {product_details["price"]}'
    # body = "ewfae"
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        print(f"Email sent successfully to {email}")
    except Exception as e:
        print(f'Error sending email: {str(e)}')
        raise
    print("send daily works")

# Function to schedule the email sending task
def schedule_email_sending(email):
    print("schedule email sending is running")
    # Schedule the email sending task every day
    scheduler.add_job(send_daily_email, 'cron', hour=17, minute=00, args=[email])
    print("chedule_email_sending works")

# Homepage route
@app.route('/')
def home():
    print("home is running")
    return render_template('index.html')
    print("home works")

# Route to handle sending email manually (for testing)
@app.route('/send-email', methods=['POST'])
def send_email():
    print("send email is running")
    email = request.json.get('email')
    send_daily_email(email)    # only for testing, remove this line later
    schedule_email_sending(email)
    print("send email works")
    return jsonify({'message': 'Email sent manually'}), 200

# Start the scheduling when the Flask app is launched
if __name__ == '__main__':
    app.run(debug=True)