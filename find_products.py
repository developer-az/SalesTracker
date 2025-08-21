#!/usr/bin/env python3
"""
Product Link Finder Tool
Helps find and test product links from various websites
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
from urllib.parse import urljoin, urlparse
import config

def test_product_link(url, website_name):
    """Test if a product link is valid and extract basic info."""
    try:
        headers = {"User-Agent": config.SCRAPING_SETTINGS["user_agent"]}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find product name
        name = "Unknown Product"
        price = "Price not found"
        
        if website_name.lower() == "lululemon":
            name_elem = soup.find("meta", attrs={'property': 'og:title'})
            price_elem = soup.find('span', class_='price')
            
            if name_elem:
                name = name_elem.get("content", "Unknown Product")
            if price_elem:
                price = price_elem.get_text(strip=True)
                
        elif website_name.lower() == "nike":
            json_ld = soup.find("script", type="application/ld+json")
            if json_ld:
                try:
                    import json
                    data = json.loads(json_ld.string)
                    name = data.get("name", "Unknown Product")
                    price_data = data.get("offers", {})
                    price = f"${price_data.get('lowPrice', 'N/A')}USD" if price_data else "Price not found"
                except:
                    pass
        
        return True, name, price
        
    except Exception as e:
        return False, f"Error: {e}", "N/A"

def find_lululemon_products():
    """Find Lululemon product links."""
    print("🔍 Finding Lululemon products...")
    
    # Common Lululemon product categories
    categories = [
        "mens-jackets-and-outerwear",
        "mens-leggings", 
        "mens-shorts",
        "mens-tops",
        "mens-pants"
    ]
    
    base_url = "https://shop.lululemon.com"
    
    for category in categories:
        try:
            url = f"{base_url}/c/{category}"
            headers = {"User-Agent": config.SCRAPING_SETTINGS["user_agent"]}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product links
                product_links = soup.find_all('a', href=re.compile(r'/p/.*'))
                
                print(f"\n📦 {category.upper()}:")
                for link in product_links[:5]:  # Show first 5 products
                    product_url = urljoin(base_url, link['href'])
                    success, name, price = test_product_link(product_url, "lululemon")
                    
                    if success:
                        print(f"  ✅ {name} - {price}")
                        print(f"     {product_url}")
                    else:
                        print(f"  ❌ {name}")
                        
        except Exception as e:
            print(f"Error accessing {category}: {e}")

def find_nike_products():
    """Find Nike product links."""
    print("🔍 Finding Nike products...")
    
    # Common Nike product categories
    categories = [
        "mens-shoes",
        "mens-clothing",
        "mens-accessories"
    ]
    
    base_url = "https://www.nike.com"
    
    for category in categories:
        try:
            url = f"{base_url}/w/{category}"
            headers = {"User-Agent": config.SCRAPING_SETTINGS["user_agent"]}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product links
                product_links = soup.find_all('a', href=re.compile(r'/t/.*'))
                
                print(f"\n📦 {category.upper()}:")
                for link in product_links[:5]:  # Show first 5 products
                    product_url = urljoin(base_url, link['href'])
                    success, name, price = test_product_link(product_url, "nike")
                    
                    if success:
                        print(f"  ✅ {name} - {price}")
                        print(f"     {product_url}")
                    else:
                        print(f"  ❌ {name}")
                        
        except Exception as e:
            print(f"Error accessing {category}: {e}")

def test_custom_link(url):
    """Test a custom product link."""
    print(f"🔍 Testing custom link: {url}")
    
    # Determine website from URL
    domain = urlparse(url).netloc.lower()
    website_name = "unknown"
    
    if "lululemon" in domain:
        website_name = "lululemon"
    elif "nike" in domain:
        website_name = "nike"
    
    success, name, price = test_product_link(url, website_name)
    
    if success:
        print(f"✅ SUCCESS!")
        print(f"   Name: {name}")
        print(f"   Price: {price}")
        print(f"   Website: {website_name}")
        return True
    else:
        print(f"❌ FAILED: {name}")
        return False

def main():
    """Main function."""
    print("🛍️  Product Link Finder Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            if len(sys.argv) > 2:
                test_custom_link(sys.argv[2])
            else:
                print("Usage: python3 find_products.py test <URL>")
        elif sys.argv[1] == "lululemon":
            find_lululemon_products()
        elif sys.argv[1] == "nike":
            find_nike_products()
        else:
            print("Unknown command. Use: test, lululemon, or nike")
    else:
        print("Usage:")
        print("  python3 find_products.py test <URL>     # Test a specific product link")
        print("  python3 find_products.py lululemon      # Find Lululemon products")
        print("  python3 find_products.py nike           # Find Nike products")
        print("\nExample:")
        print("  python3 find_products.py test https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786")

if __name__ == "__main__":
    main()
