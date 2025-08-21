# Sale Tracker – Email Notifier

A robust Python web app that scrapes product prices from Lululemon and Nike and emails personalized daily updates. Deployed on Render with a secure GitHub Actions cron.

## 🚀 Features

- Minimal web UI: enter your email and product URLs
- Personalized daily email (9 PM UTC by default)
- Secure cron endpoint protected by `CRON_TOKEN`
- Tests, logging, and error handling

## 📋 Prerequisites

- Python 3.8+
- Gmail App Password for sending emails

## 🛠️ Install (dev)

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

- Web service start: `bash -lc "gunicorn -b 0.0.0.0:$PORT web_app:app & python -c 'import main_improved as m; m.run_scheduler()'"`
- Render env: `SENDER_EMAIL`, `EMAIL_PASSWORD`, `FLASK_ENV=production`, `CRON_TOKEN` (same value as below)
- GitHub Actions secrets: `APP_URL`, `CRON_TOKEN`

Daily workflow: `.github/workflows/daily-email.yml` (runs at 21:00 UTC)

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
