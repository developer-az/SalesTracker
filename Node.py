from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from apscheduler.schedulers.blocking import BlockingScheduler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from get_product_details import get_product_details
from bs4 import BeautifulSoup
#from dotenv import load_dotenv #remove for deployment onto heroku
import os
import smtplib
import requests

#load_dotenv() #remove for deployment onto heroku
app = Flask(__name__)
CORS(app)

scheduler = BlockingScheduler()

product_url = 'https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786?color=0001'

def get_product_details(product_url):
    response = requests.get(product_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    name_element = soup.find('h1', class_='product-title_title__i8NUw').find('div')
    price_element = soup.find('span', class_='price')
        
    product_name = name_element.get_text().strip() if name_element else 'Product name not found'
    product_price = price_element.get_text().strip() if price_element else 'Price not found'
    return product_name, product_price

def send_product_details_email(email):

    sender_email = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    product_details = {}

    if not product_details:
        product_details['name'], product_details['price'] = get_product_details(product_url)

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

def schedule_email_sending(email): 
    scheduler.add_job(send_product_details_email, 'cron', hour=14, minute=20, args=[email])
    scheduler.start()

@app.route('/')
def home():
    return render_template('website.html')

@app.route('/send-email', methods=['POST']) 
def send_email():
    email = request.json.get('email')
    send_product_details_email(email) #for testing
    schedule_email_sending(email)
    return jsonify({'message': 'Email sent manually'}), 200

if __name__ == '__main__':
    app.run(debug=True)