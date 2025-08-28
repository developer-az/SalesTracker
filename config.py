"""
Configuration file for Sale Tracker
"""

# Product links to track
PRODUCT_LINKS = {
    "lululemon": [
        "https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786?color=0001",
        "https://shop.lululemon.com/p/mens-jackets-and-outerwear/Pace-Breaker-Jacket/_/prod11670131?cid=Google_SHOP_US_NAT_EN_X_BrandShop_Incr-All_OMNI_GEN_Y24_ag-SHOP_G_US_EN_DM_M_GEN_NO_Tops-Jackets&color=0001&gad_campaignid=21471260535&gad_source=1&gbraid=0AAAAADL8Avk5CDt35HKBgpfRSuD0CpJvP&gclid=CjwKCAjwkbzEBhAVEiwA4V-yqpMcLNT4qAeAlXO9G-dH0QPZKbelVx2jrlqZrfrChowBqSPFpaclcxoCx5oQAvD_BwE&gclsrc=aw.ds&locale=en_US&sl=US&sz=S",
    ],
    "nike": ["https://www.nike.com/t/unlimited-mens-repel-hooded-versatile-jacket-56pDjs/FB7551-010"],
}

# Email settings
EMAIL_SETTINGS = {"smtp_server": "smtp.gmail.com", "smtp_port": 587, "schedule_time": "21:00"}  # 9 PM

# Scraping settings
SCRAPING_SETTINGS = {
    "timeout": 10,
    "retry_attempts": 3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}
