import requests
from bs4 import BeautifulSoup

def get_product_details(product_url):
    response = requests.get(product_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    name_element = soup.find('h1', class_='product-title_title__i8NUw').find('div')
    price_element = soup.find('span', class_='price')
        
    product_name = name_element.get_text().strip() if name_element else 'Product name not found'
    product_price = price_element.get_text().strip() if price_element else 'Price not found'
    return product_name, product_price