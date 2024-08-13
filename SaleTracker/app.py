from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv 

load_dotenv() 
app = Flask(__name__)
CORS(app)

scheduler = BackgroundScheduler()
product_link = ""
product_details = {}

# Function to get product details
def get_product_details():
    
    response = requests.get(product_link)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    name_element = soup.find("meta", attrs={'property': 'og:title'})
    price_element = soup.find('span', class_='price') 
    print(name_element.get("content"))
    print(price_element)
    if name_element:
        product_name = name_element.get("content")
    else:
        product_name = 'Product name not found'
    if price_element:
        product_price = price_element.get_text().strip() 
    else:
        product_price = 'Price not found'

    return product_name, product_price

# Function to check if the product is on sale
def get_product_sales():
    response = requests.get(product_link)
    soup = BeautifulSoup(response.content, 'html.parser')

    sale_label = soup.find('div', class_='sale-label')  # Example: Class name might vary
    original_price_element = soup.find('span', class_='original-price')  # Example: Class name might vary
    discounted_price_element = soup.find('span', class_='discounted-price')  # Example: Class name might vary
    #and (original_price_element != discounted_price_element)
    if sale_label or (original_price_element and discounted_price_element):
        print(sale_label)
        print(original_price_element)
        print(discounted_price_element)
        return True
    else:
        return False

# Function to send email
def send_email(recipient_email):

    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('EMAIL_PASSWORD')

    product_details['name'], product_details['price'] = get_product_details()
    # get_product_sales()
    # product_details['sale'] = get_product_sales()
    print(product_details)
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = 'Your Product ' + product_details['name'] + ' is on sale!'
    body = f"The price of {product_details['name']} is: {product_details['price']}"
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

# Homepage route
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/schedule-email', methods=['POST']) 
def schedule_email():
    try:
        recipient_email = request.json.get('recipient_email')
        send_email(recipient_email)    #for debuging
        if not scheduler.running:
            scheduler.add_job(send_email, 'cron', hour=15, minute=23, args=[recipient_email])
            scheduler.start()
        return jsonify({'message': 'Email sent manually'}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Failed to send email'}), 500

@app.route('/update-product-link', methods=['POST'])
def update_product_link():
    try:
        global product_link
        product_link = request.json.get('productLink')
        product_details.clear()  # Clear the cached product details
        return jsonify({'message': 'Product link updated successfully'}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Failed to update product link'}), 500

if __name__ == '__main__':
    app.run(debug=True)