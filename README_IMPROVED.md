# Sale Tracker – Improved Email Notifier

A robust Python application that scrapes product prices from Lululemon and Nike, then sends combined daily email alerts to one or more recipients. This improved version includes better error handling, logging, configuration management, and a command-line interface.

## 🚀 Features

* **Robust Scraping**: Scrapes product names, prices, and images from Lululemon and Nike
* **Email Notifications**: Sends beautifully formatted HTML emails with product information
* **Scheduled Delivery**: Automatically sends emails daily at 9 PM
* **Error Handling**: Comprehensive error handling and logging
* **Configuration Management**: Easy-to-modify configuration file
* **Command-Line Interface**: User-friendly CLI for testing and management
* **Test Suite**: Comprehensive tests for all functionality
* **Logging**: Detailed logging for debugging and monitoring
* **Cross-Platform**: Works on macOS, Linux, and Windows

## 📋 Prerequisites

* Python 3.8 or higher
* Gmail account with App Password (for sending emails)
* Internet connection to access product pages

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd SaleTracker
```

### 2. Install Dependencies

```bash
pip3 install --break-system-packages -r requirements.txt
```

### 3. Configure Environment Variables

Create or update your `.env` file:

```env
SENDER_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient1@example.com
RECIPIENT_EMAIL2=recipient2@example.com  # Optional
```

**Note**: For Gmail, you must:
1. Enable 2-Step Verification
2. Generate an App Password under Google Account > Security > App Passwords

## 🎯 Usage

### Command-Line Interface

The improved version includes a comprehensive CLI:

```bash
# Test scraping functionality
python3 cli.py test-scraping

# Send a test email
python3 cli.py send-test

# Show current configuration
python3 cli.py show-config

# Start the scheduler
python3 cli.py run

# Start with verbose logging
python3 cli.py run --verbose
```

### Direct Script Execution

```bash
# Run the improved version
python3 main_improved.py

# Run tests
python3 test_sale_tracker.py
```

## ⚙️ Configuration

### Product Links

Edit `config.py` to modify product links:

```python
PRODUCT_LINKS = {
    "lululemon": [
        "https://shop.lululemon.com/p/your-product-link",
        # Add more Lululemon products...
    ],
    "nike": [
        "https://www.nike.com/t/your-product-link",
        # Add more Nike products...
    ]
}
```

### Email Settings

```python
EMAIL_SETTINGS = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "schedule_time": "21:00"  # 9 PM
}
```

### Scraping Settings

```python
SCRAPING_SETTINGS = {
    "timeout": 10,  # Request timeout in seconds
    "retry_attempts": 3,
    "user_agent": "Your custom user agent"
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_sale_tracker.py
```

The test suite includes:
- Unit tests for all functions
- Mock tests for error scenarios
- Integration tests with live websites
- Configuration validation

## 📊 Logging

The application creates detailed logs in `sale_tracker.log`:

```
2025-08-21 14:30:00,123 - INFO - Starting Sale Tracker scheduler
2025-08-21 14:30:01,456 - INFO - Successfully scraped Lululemon product: Product Name - $100USD
2025-08-21 14:30:02,789 - INFO - Email sent successfully to recipient@example.com
```

## 🔧 Building for Distribution

### macOS App (using py2app)

```bash
python3 setup_improved.py py2app
```

The built app will be in `dist/Sale Tracker.app`

### Linux/Windows Executable

```bash
# Install PyInstaller
pip3 install --break-system-packages pyinstaller

# Build executable
pyinstaller --onefile --add-data "config.py:." --add-data ".env:." main_improved.py
```

## 🏗️ Project Structure

```
SaleTracker/
├── main_improved.py      # Improved main application
├── config.py            # Configuration management
├── cli.py               # Command-line interface
├── test_sale_tracker.py # Comprehensive test suite
├── setup_improved.py    # Build configuration
├── requirements.txt     # Dependencies
├── .env                 # Environment variables
├── README_IMPROVED.md   # This file
└── deprecated/          # Original version files
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip3 install --break-system-packages -r requirements.txt
   ```

2. **Email Authentication**: Verify your Gmail App Password is correct

3. **Scraping Failures**: Check internet connection and product URLs

4. **Permission Errors**: Ensure write permissions for log files

### Debug Mode

Run with verbose logging:

```bash
python3 cli.py run --verbose
```

### Manual Testing

Test individual components:

```bash
# Test scraping
python3 cli.py test-scraping

# Test email
python3 cli.py send-test
```

## 🔄 Improvements Over Original Version

- **Better Error Handling**: Graceful handling of network errors and missing data
- **Configuration Management**: Centralized configuration in `config.py`
- **Logging**: Comprehensive logging for debugging and monitoring
- **CLI Interface**: User-friendly command-line interface
- **Test Suite**: Comprehensive tests for all functionality
- **Dynamic Subject Lines**: Subject lines based on actual scraped prices
- **Improved Email Formatting**: Better HTML email design
- **Environment Variable Validation**: Proper validation of required settings
- **Type Hints**: Better code documentation and IDE support

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `sale_tracker.log`
3. Run the test suite to identify issues
4. Create an issue in the repository
