# Sale Tracker – Email Notifier

A robust Python web app that scrapes product prices from Lululemon and Nike and emails personalized daily updates. Deployed on Render with a secure GitHub Actions cron.

## 🚀 Features

- Minimal web UI: enter your email and product URLs
- Personalized daily email (9 PM UTC by default)
- Secure cron endpoint protected by `CRON_TOKEN`
- Tests, logging, and error handling
- **Comprehensive health checks and diagnostics**
- **Automated deployment with GitHub Actions**

## 📋 Prerequisites

- Python 3.8+
- Gmail App Password for sending emails
- Hosting service account (Render recommended)

## ⚡ Quick Start

📖 **For a complete setup guide, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

1. Deploy to Render (or similar service)
2. Set environment variables (`SENDER_EMAIL`, `EMAIL_PASSWORD`, `CRON_TOKEN`)  
3. Configure GitHub Actions secrets (`APP_URL`, `CRON_TOKEN`)
4. Test with health check: `/api/health`

❓ **Do I need the app "open"?** No! Once deployed, it runs automatically 24/7.

## 🛠️ Local Development

```bash
pip3 install --break-system-packages -r requirements.txt
```

Create `.env` (local dev only):
```env
SENDER_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

## 🎯 Usage (Web)

1) Enter Your Email → Save Email
2) Enter Product URL (Lululemon/Nike) → Add Product
3) You’ll receive a personalized email daily at 21:00 UTC

Force-send once:
```bash
curl -s -X POST -H "X-CRON-TOKEN: <TOKEN>" "https://<your-app-url>/api/cron/send"
```

## ☁️ Deploy (Render + GitHub Actions)

**📖 See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete deployment instructions**

Quick summary:
- **Render env**: `SENDER_EMAIL`, `EMAIL_PASSWORD`, `FLASK_ENV=production`, `CRON_TOKEN`
- **GitHub Actions secrets**: `APP_URL`, `CRON_TOKEN` (same value as Render)
- **Start command**: `gunicorn -b 0.0.0.0:$PORT web_app:app`

Daily workflow: `.github/workflows/daily-email.yml` (runs at 21:00 UTC)

### Health Check
Once deployed, verify setup:
```bash
curl https://your-app-url/api/health
```

## 🧪 Tests

```bash
python3 test_sale_tracker.py
python3 test_web_app.py
```

## 🏗️ Structure

```
SaleTracker/
├── web_app.py          # Flask web server + API
├── main_improved.py    # Email + scraping logic
├── templates/dashboard.html
├── recipients_store.py
├── subscriptions_store.py
├── .github/workflows/daily-email.yml
└── README.md
```

## 🔐 Notes

- Set the same `CRON_TOKEN` on Render and GitHub Actions
- Use a long random token in production (not `1`)
