# Sale Tracker – Email Notifier

A small Python web app that reads live product prices from storefronts, shows them in a simple dashboard, and emails a daily digest. Deployed on Render with a secure GitHub Actions cron.

## 🚀 Features

- Two-field setup: email + product URL, then live prices
- Works with Nike, Lululemon and most stores that publish JSON-LD / Open Graph product data
- Correct price parsing (handles Nike `ProductGroup` variants and sale prices)
- Per-product status: live price, price missing, or retailer blocked
- Personalized daily email (9 PM UTC by default)
- Secure cron endpoint protected by `CRON_TOKEN`
- Tests, logging, and error handling
- Health checks and diagnostics at `/api/health`

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

1. Enter your email and a product URL → **Start tracking**
2. The dashboard shows the product's current price and image
3. Add more links any time, refresh prices, or remove products
4. You'll receive a personalized email daily at 21:00 UTC

Force-send once:
```bash
curl -s -X POST -H "X-CRON-TOKEN: <TOKEN>" "https://<your-app-url>/api/cron/send"
```

### How scraping works

`scraper.py` fetches the product page and reads structured product data
(JSON-LD `Product` / `ProductGroup`, microdata, Open Graph, then common price
markup). It uses `curl_cffi` with a real browser TLS fingerprint first and falls
back to `requests`. Nothing is hard-coded per retailer, so most stores work.

Some retailers (Lululemon in particular) block datacenter IPs. When that happens
the product card says **Blocked** and keeps the name from the URL; the daily
email retries the price. Nike works reliably.

If a site blocks your host, the fix is a residential/rotating proxy in
`scraper._fetch`.

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
├── scraper.py          # Product data fetching and parsing
├── main_improved.py    # Email digest logic
├── templates/dashboard.html
├── recipients_store.py
├── subscriptions_store.py
├── .github/workflows/daily-email.yml
└── README.md
```

## 🔐 Notes

- Set the same `CRON_TOKEN` on Render and GitHub Actions
- Use a long random token in production (not `1`)
