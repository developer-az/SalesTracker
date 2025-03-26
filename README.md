# Sale Tracker

A Flask application that tracks product prices and sends email notifications when products go on sale.

## Features

- Track product prices from any website
- Email notifications for price changes
- Scheduled price checks
- Rate limiting to prevent abuse
- Health check endpoint
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- Gmail account (for sending notifications)
- Virtual environment (recommended)

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd SaleTracker
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
SENDER_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
PORT=5000  # Optional, defaults to 5000
```

Note: For Gmail, you'll need to use an App Password. To generate one:
1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled
4. Go to App Passwords
5. Generate a new app password for "Mail"

## Running Locally

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

### Using Gunicorn (Recommended for Production)

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Run the application:
```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

### Using Docker

1. Build the Docker image:
```bash
docker build -t sale-tracker .
```

2. Run the container:
```bash
docker run -p 5000:5000 --env-file .env sale-tracker
```

## API Endpoints

- `GET /`: Homepage
- `GET /health`: Health check endpoint
- `POST /schedule-email`: Schedule email notifications
  ```json
  {
    "recipient_email": "user@example.com"
  }
  ```
- `POST /update-product-link`: Update the product to track
  ```json
  {
    "productLink": "https://example.com/product"
  }
  ```

## Rate Limiting

The API has the following rate limits:
- 200 requests per day
- 50 requests per hour
- 5 requests per minute for specific endpoints

## Error Handling

The application includes comprehensive error handling for:
- Invalid email addresses
- Invalid product links
- Network errors
- Email sending failures
- Missing environment variables

## Logging

Logs are written to the console with the following format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.