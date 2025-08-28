"""
Enhanced configuration management with performance settings and retailer support.
"""

import os
from datetime import datetime
from typing import Any, Dict, List

# Product links to track (organized by retailer)
PRODUCT_LINKS = {
    "lululemon": [
        "https://shop.lululemon.com/p/mens-jackets-and-outerwear/Down-For-It-All-Hoodie/_/prod9200786?color=0001",
        "https://shop.lululemon.com/p/mens-jackets-and-outerwear/Pace-Breaker-Jacket/_/prod11670131?cid=Google_SHOP_US_NAT_EN_X_BrandShop_Incr-All_OMNI_GEN_Y24_ag-SHOP_G_US_EN_DM_M_GEN_NO_Tops-Jackets&color=0001&gad_campaignid=21471260535&gad_source=1&gbraid=0AAAAADL8Avk5CDt35HKBgpfRSuD0CpJvP&gclid=CjwKCAjwkbzEBhAVEiwA4V-yqpMcLNT4qAeAlXO9G-dH0QPZKbelVx2jrlqZrfrChowBqSPFpaclcxoCx5oQAvD_BwE&gclsrc=aw.ds&locale=en_US&sl=US&sz=S",
    ],
    "nike": ["https://www.nike.com/t/unlimited-mens-repel-hooded-versatile-jacket-56pDjs/FB7551-010"],
}

# Email settings
EMAIL_SETTINGS = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "schedule_time": "21:00",  # 9 PM
    "max_retries": 3,
    "retry_delay": 5,  # seconds
}

# Enhanced scraping settings
SCRAPING_SETTINGS = {
    "timeout": 15,  # Increased for better reliability
    "retry_attempts": 3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "rate_limit_delay": 1.5,  # Delay between requests in seconds
    "enable_cache": True,
    "cache_ttl": 3600,  # 1 hour cache TTL
    "max_concurrent_requests": 5,
}

# Performance and monitoring settings
PERFORMANCE_SETTINGS = {
    "enable_metrics": True,
    "enable_structured_logging": True,
    "log_level": "INFO",
    "max_log_file_size": 10 * 1024 * 1024,  # 10MB
    "log_retention_days": 30,
    "health_check_interval": 300,  # 5 minutes
    "enable_profiling": False,  # Set to True for performance analysis
}

# Security settings
SECURITY_SETTINGS = {
    "enable_rate_limiting": True,
    "max_requests_per_minute": 60,
    "enable_input_validation": True,
    "enable_csrf_protection": True,
    "session_timeout": 3600,  # 1 hour
    "max_email_recipients": 100,
    "max_subscriptions_per_user": 50,
}

# Database/Storage settings
STORAGE_SETTINGS = {
    "storage_type": "file",  # "file" or "database"
    "data_directory": "data",
    "backup_enabled": True,
    "backup_interval": 24 * 3600,  # 24 hours
    "compression_enabled": True,
}

# Feature flags
FEATURE_FLAGS = {
    "enable_web_ui": True,
    "enable_cli": True,
    "enable_api": True,
    "enable_webhooks": False,
    "enable_analytics": True,
    "enable_notifications": True,
    "enable_user_authentication": False,  # Future feature
}

# Retailer-specific settings
RETAILER_SETTINGS = {
    "lululemon": {
        "timeout": 15,
        "retry_attempts": 3,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "rate_limit": 2.0,  # seconds between requests
        "cache_ttl": 1800,  # 30 minutes
        "price_selectors": ['[data-testid="product-price"]', ".price", ".product-price"],
    },
    "nike": {
        "timeout": 20,
        "retry_attempts": 4,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "rate_limit": 1.5,  # seconds between requests
        "cache_ttl": 1800,  # 30 minutes
        "price_selectors": ['[data-test="product-price"]', ".product-price", ".notranslate"],
    },
}


def get_config() -> Dict[str, Any]:
    """Get complete configuration as dictionary."""
    return {
        "product_links": PRODUCT_LINKS,
        "email": EMAIL_SETTINGS,
        "scraping": SCRAPING_SETTINGS,
        "performance": PERFORMANCE_SETTINGS,
        "security": SECURITY_SETTINGS,
        "storage": STORAGE_SETTINGS,
        "features": FEATURE_FLAGS,
        "retailers": RETAILER_SETTINGS,
        "version": "2.1.0",
        "last_updated": datetime.now().isoformat(),
    }


def get_retailer_config(retailer_name: str) -> Dict[str, Any]:
    """Get configuration for a specific retailer."""
    retailer_config = RETAILER_SETTINGS.get(retailer_name, {})

    # Merge with global scraping settings as fallback
    config = SCRAPING_SETTINGS.copy()
    config.update(retailer_config)

    return config


def validate_config() -> List[str]:
    """Validate configuration and return list of issues."""
    issues = []

    # Validate required settings
    required_env_vars = ["SENDER_EMAIL", "EMAIL_PASSWORD"]
    for var in required_env_vars:
        if not os.getenv(var):
            issues.append(f"Missing required environment variable: {var}")

    # Validate product links
    if not PRODUCT_LINKS or not any(PRODUCT_LINKS.values()):
        issues.append("No product links configured")

    # Validate email settings
    if EMAIL_SETTINGS.get("smtp_port", 0) not in [25, 587, 465]:
        issues.append("Invalid SMTP port configuration")

    # Validate scraping settings
    if SCRAPING_SETTINGS.get("timeout", 0) < 5:
        issues.append("Scraping timeout too low (minimum 5 seconds recommended)")

    if SCRAPING_SETTINGS.get("retry_attempts", 0) < 1:
        issues.append("Retry attempts must be at least 1")

    return issues


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature flag is enabled."""
    return FEATURE_FLAGS.get(feature, False)


# Backward compatibility - maintain the original variable names
# This ensures existing code continues to work
ORIGINAL_SCRAPING_SETTINGS = {
    "timeout": SCRAPING_SETTINGS["timeout"],
    "retry_attempts": SCRAPING_SETTINGS["retry_attempts"],
    "user_agent": SCRAPING_SETTINGS["user_agent"],
}
