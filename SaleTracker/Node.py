from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv 

load_dotenv() 
app = Flask(__name__)
CORS(app)

scheduler = BlockingScheduler()
product_url = ""
product_details = {}

# Function to get product details
def get_product_details():
    
    response = requests.get(product_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    name_element = soup.find('h1', class_='product-title_title__i8NUw').find('div') 
    price_element = soup.find('span', class_='price') 
    
    if name_element:
        product_name = name_element.get_text().strip()
    else:
        product_name = 'Product name not found'
    if price_element:
        product_price = price_element.get_text().strip() 
    else:
        product_price = 'Price not found'

    return product_name, product_price
    

# Function to send daily email
def send_email(email):

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

# Homepage route
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/schedule-email', methods=['POST']) 
def schedule_email():
    try:
        email = request.json.get('email')
        send_email(email)    #for debuging
        # scheduler.add_job(send_email, 'cron', hour=15, minute=23, args=[email])
        # scheduler.start()
        return jsonify({'message': 'Email sent manually'}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Failed to send email'}), 500

@app.route('/update-product-link', methods=['POST'])
def update_product_link():
    try:
        global product_url
        product_url = request.json.get('productLink')
        product_details.clear()  # Clear the cached product details
        return jsonify({'message': 'Product link updated successfully'}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Failed to update product link'}), 500

if __name__ == '__main__':
    app.run(debug=True)