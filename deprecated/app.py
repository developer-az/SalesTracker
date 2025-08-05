from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
import re
from urllib.parse import urlparse
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize scheduler
scheduler = BackgroundScheduler()

# Global state
class ProductState:
    def __init__(self):
        self.link = ""
        self.details = {}

product_state = ProductState()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url):
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_product_details():
    """Get product details with error handling"""
    try:
        if not product_state.link:
            raise ValueError("Product link not set")
            
        response = requests.get(product_state.link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        name_element = soup.find("meta", attrs={'property': 'og:title'})
        price_element = soup.find('span', class_='price')
        
        if not name_element:
            raise ValueError("Product name not found")
        if not price_element:
            raise ValueError("Price not found")
            
        product_name = name_element.get("content")
        product_price = price_element.get_text().strip()
        
        return product_name, product_price
    except requests.RequestException as e:
        logger.error(f"Error fetching product details: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_product_details: {str(e)}")
        raise

def get_product_sales():
    """Check if product is on sale with error handling"""
    try:
        if not product_state.link:
            raise ValueError("Product link not set")
            
        response = requests.get(product_state.link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        sale_label = soup.find('div', class_='sale-label')
        original_price_element = soup.find('span', class_='original-price')
        discounted_price_element = soup.find('span', class_='discounted-price')

        return bool(sale_label or (original_price_element and discounted_price_element))
    except Exception as e:
        logger.error(f"Error checking product sales: {str(e)}")
        return False

def send_email(recipient_email):
    """Send email with error handling"""
    try:
        sender_email = os.environ.get('SENDER_EMAIL')
        sender_password = os.environ.get('EMAIL_PASSWORD')

        if not sender_email or not sender_password:
            raise ValueError("Email credentials not properly configured")

        if not product_state.link:
            raise ValueError("Please set a product link first")

        logger.info(f"Fetching product details for link: {product_state.link}")
        product_state.details['name'], product_state.details['price'] = get_product_details()
        product_state.details['sale'] = get_product_sales()
        
        logger.info(f"Product details fetched: {product_state.details}")

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = f'Product Update: {product_state.details["name"]}'
        
        body = f"""
        Product: {product_state.details['name']}
        Current Price: {product_state.details['price']}
        On Sale: {'Yes' if product_state.details['sale'] else 'No'}
        Check it out here: {product_state.link}
        """
        
        message.attach(MIMEText(body, 'plain'))

        logger.info(f"Attempting to send email to {recipient_email}")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
            
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {str(e)}")
        raise ValueError("Invalid email credentials. Please check your Gmail app password.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {str(e)}")
        raise ValueError(f"Failed to send email: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise ValueError(f"Unexpected error: {str(e)}")

@app.route('/')
def home():
    """Homepage route"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/schedule-email', methods=['POST'])
@limiter.limit("5 per minute")
def schedule_email():
    """Schedule email with validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        recipient_email = data.get('recipient_email')
        if not recipient_email or not validate_email(recipient_email):
            return jsonify({'error': 'Invalid email address'}), 400

        if not product_state.link:
            return jsonify({'error': 'Please set a product link first'}), 400

        # Send a test email immediately
        try:
            send_email(recipient_email)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f"Failed to send email: {str(e)}"}), 500

        # Schedule the email
        if not scheduler.running:
            scheduler.add_job(send_email, 'cron', hour=15, minute=23, args=[recipient_email])
            scheduler.start()
            
        return jsonify({
            'message': 'Email sent successfully and scheduled for daily updates',
            'product': product_state.details
        }), 200
    except Exception as e:
        logger.error(f"Error scheduling email: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/update-product-link', methods=['POST'])
@limiter.limit("5 per minute")
def update_product_link():
    """Update product link with validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        new_link = data.get('productLink')
        if not new_link or not validate_url(new_link):
            return jsonify({'error': 'Invalid product link'}), 400

        product_state.link = new_link
        product_state.details.clear()
        
        # Test the link immediately
        get_product_details()
        
        return jsonify({'message': 'Product link updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating product link: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Register scheduler shutdown
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # Use environment variable for port
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)