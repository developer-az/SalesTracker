# Sale Tracker Setup Guide

This comprehensive guide will help you set up the Sale Tracker application so that daily emails work correctly with GitHub Actions.

## 🎯 Quick Setup Checklist

- [ ] Set up email credentials (SENDER_EMAIL, EMAIL_PASSWORD)
- [ ] Add email recipients 
- [ ] Deploy to hosting service (Render recommended)
- [ ] Configure GitHub Actions secrets
- [ ] Test the setup
- [ ] Verify daily emails are working

## 📧 Step 1: Email Configuration

### Gmail Setup (Recommended)
1. **Create Gmail App Password**:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Factor Authentication if not already enabled
   - Go to "2-Step Verification" → "App passwords"
   - Generate an app password for "Mail"
   - Copy the 16-character password (no spaces)

2. **Set Environment Variables**:
   ```env
   SENDER_EMAIL=your-email@gmail.com
   EMAIL_PASSWORD=your-16-char-app-password
   ```

## 👥 Step 2: Add Recipients

You have two options to add recipients:

### Option A: Via Web Interface (Recommended)
1. Start the web application
2. Go to `http://localhost:5000`
3. Enter email addresses and product URLs
4. Recipients are stored persistently

### Option B: Via Environment Variables
```env
RECIPIENT_EMAIL=recipient1@example.com
RECIPIENT_EMAIL2=recipient2@example.com
```

## ☁️ Step 3: Deploy to Hosting Service

### Render Deployment (Recommended)

1. **Create Render Account**: Go to [render.com](https://render.com)

2. **Connect GitHub Repository**:
   - Fork or clone this repository to your GitHub account
   - Connect your GitHub account to Render
   - Create a new "Web Service" from your repository

3. **Configure Render Environment**:
   ```env
   SENDER_EMAIL=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   FLASK_ENV=production
   CRON_TOKEN=your-long-random-token-here
   ```

4. **Set Build Command**: 
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Start Command**:
   ```bash
   gunicorn -b 0.0.0.0:$PORT web_app:app
   ```

6. **Deploy and Note Your App URL**: 
   - Example: `https://your-app-name.onrender.com`

### Alternative: Heroku, Railway, or Other PaaS
Similar steps apply to other platforms. Key requirements:
- Python 3.8+ runtime
- Install dependencies from `requirements.txt`
- Run with `gunicorn web_app:app`
- Set the environment variables listed above

## 🔧 Step 4: Configure GitHub Actions

1. **Go to Your Repository Settings**:
   - Navigate to `Settings` → `Secrets and variables` → `Actions`

2. **Add Repository Secrets**:
   ```
   APP_URL: https://your-app-name.onrender.com
   CRON_TOKEN: your-long-random-token-here
   ```
   ⚠️ **Important**: Use the SAME token for both Render and GitHub!

3. **Verify Workflow File**: 
   Ensure `.github/workflows/daily-email.yml` exists and contains:
   ```yaml
   name: Daily Personalized Emails
   
   on:
     schedule:
       - cron: '0 21 * * *' # 9 PM UTC daily
     workflow_dispatch: {}
   
   jobs:
     trigger:
       runs-on: ubuntu-latest
       steps:
         - name: Call secure cron endpoint
           run: |
             curl -s -X POST \
               -H "X-CRON-TOKEN: ${{ secrets.CRON_TOKEN }}" \
               "${{ secrets.APP_URL }}/api/cron/send" || exit 1
   ```

## ✅ Step 5: Test Your Setup

### Test Email Configuration
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"your-test-email@example.com"}' \
  https://your-app-name.onrender.com/api/test-email
```

### Test Health Check
```bash
curl https://your-app-name.onrender.com/api/health
```

### Test Manual Cron Trigger
```bash
curl -X POST -H "X-CRON-TOKEN: your-token" \
  https://your-app-name.onrender.com/api/cron/send
```

### Test GitHub Actions
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Find "Daily Personalized Emails" workflow
4. Click "Run workflow" to trigger manually
5. Check the workflow logs for any errors

## 📋 Step 6: Verify Daily Operation

### Monitoring
- **Health Check**: `GET /api/health` - Shows configuration status
- **Status Check**: `GET /api/status` - Shows last email sent time
- **Logs**: Check your hosting service logs for errors

### Expected Behavior
- ✅ Workflow runs daily at 21:00 UTC (9 PM)
- ✅ Health check shows "healthy" or "degraded" (not "unhealthy") 
- ✅ Recipients receive daily email with product updates
- ✅ Logs show "Daily emails sent successfully"

## ❓ FAQ: "Do I need the app open?"

**No!** Once deployed to a hosting service (like Render):

1. **The app runs 24/7** on the hosting service's servers
2. **GitHub Actions triggers it daily** via HTTP request
3. **You don't need to keep anything open** on your computer
4. **The workflow is completely automated**

The confusion often comes from local development - that's only for testing!

## 🚨 Troubleshooting

### Common Issues

#### "Unauthorized" Error
- Check that `CRON_TOKEN` matches between Render and GitHub secrets
- Verify the token is set correctly (no extra spaces)

#### "No recipients configured"
- Add recipients via web interface OR set `RECIPIENT_EMAIL` environment variable
- Check `/api/health` endpoint to verify recipient configuration

#### "Email configuration error"
- Verify `SENDER_EMAIL` and `EMAIL_PASSWORD` are set correctly
- For Gmail, ensure you're using an App Password, not regular password
- Test with `/api/test-email` endpoint

#### "Email sending failed" 
- Check email server settings in `config.py`
- Verify network connectivity on hosting service
- Check hosting service logs for detailed error messages

#### GitHub Actions Not Running
- Verify repository secrets are set correctly
- Check workflow file syntax in `.github/workflows/daily-email.yml`
- Ensure app URL is accessible and returns 200 status

### Debug Commands

```bash
# Check app status
curl https://your-app-name.onrender.com/api/status

# Check configuration health
curl https://your-app-name.onrender.com/api/health

# Test email sending
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' \
  https://your-app-name.onrender.com/api/test-email

# Manual trigger (use your token)
curl -X POST -H "X-CRON-TOKEN: your-token" \
  https://your-app-name.onrender.com/api/cron/send
```

## 📞 Getting Help

If you're still having issues:

1. **Check the health endpoint**: `/api/health` shows exactly what's missing
2. **Look at hosting logs**: Most deployment issues show up in server logs  
3. **Test email configuration**: Use `/api/test-email` to verify email works
4. **Verify GitHub secrets**: Make sure `APP_URL` and `CRON_TOKEN` are set correctly

The system is designed to be self-diagnosing - the health check will tell you exactly what needs to be fixed!