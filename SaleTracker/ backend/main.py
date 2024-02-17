from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from apscheduler.schedulers.blocking import BlockingScheduler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from get_product_details import get_product_details
#from dotenv import load_dotenv #remove for deployment onto heroku
import os
import smtplib

#load_dotenv() #remove for deployment onto heroku
app = Flask(__name__)
CORS(app)

scheduler = BlockingScheduler()

product_url = 'https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786?color=0001'

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
    scheduler.add_job(send_product_details_email, 'cron', hour=14, minute=12, args=[email])
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