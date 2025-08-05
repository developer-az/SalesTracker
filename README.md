# Sale Tracker – Email Notifier

A simple Python script that scrapes product prices from Lululemon and Nike, then sends combined daily email alerts to one or more recipients.

This project is packaged using `py2app` to create a standalone macOS `.app` file that runs the script daily.

---

## Features

* Scrapes product names and prices from Lululemon and Nike
* Sends email alerts to a list of recipients once per day at 9 PM
* Formats a combined email with prices and product links
* Easily buildable into a standalone `.app` using `py2app` on macOS

---

## Prerequisites

* Python 3.8 or higher
* macOS (for building `.app` with `py2app`)
* Gmail account (App Password required for sending emails)
* Internet connection to access product pages

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd SaleTracker
```

### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If not already included, install `py2app` manually:

```bash
pip install py2app
```

### 4. Create a `.env` File

Create a `.env` file in the project root with the following variables:

```env
SENDER_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient1@example.com
RECIPIENT_EMAIL2=recipient2@example.com
```

Note: For Gmail, you must enable 2-Step Verification and generate an App Password under Google Account > Security > App Passwords.

---

## Running the Script (Dev Mode)

To test the email script directly:

```bash
python3 send_email.py
```

This will begin checking prices and emailing once per day at 9:00 PM.

To stop it, press `Ctrl + C`.

---

## Building a macOS App

Use `py2app` to package the script into a `.app` file.

### 1. Build the App

```bash
python3 setup.py py2app
```

### 2. Locate the Built App

After building, the `.app` will be located in the `dist/` directory:

```
dist/send_email.app
```

You can move this to `/Applications` or run it directly. It will run in the background and send emails daily.

---

## Security

* Avoid committing your `.env` file to version control.
* Use App Passwords instead of your main Gmail password.
* Do not hardcode credentials in the script.
