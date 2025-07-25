# Google Cloud Setup Guide for DocuMind

## 🆕 Complete Google Cloud Setup (Step-by-Step)

This guide will walk you through setting up Google Cloud from scratch for deploying your DocuMind backend.

## Phase 1: Google Cloud Account Setup

### 1. Create Google Cloud Account
1. Go to https://console.cloud.google.com
2. Sign in with your Google account (or create one)
3. Accept the terms of service
4. **Important**: You'll get $300 in free credits for new accounts!

### 2. Create Your First Project
1. Click "Select a project" at the top
2. Click "New Project"
3. Project name: `documind-backend` (or any name)
4. Project ID: Must be globally unique (suggestion: `documind-backend-2024`)
5. Click "Create"
6. **Remember your Project ID** - you'll need it!

### 3. Set Up Billing (Required)
1. Go to Billing in the left sidebar
2. Set up billing account (credit card required)
3. **Good news**: Cloud Run has generous free tier!
   - 2 million requests/month free
   - 1GB outbound data/month free
   - 360,000 GB-seconds of compute time free

## Phase 2: Install Google Cloud CLI

### Windows Installation
1. Download Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Run the installer (google-cloud-sdk.msi)
3. During installation, check "Add to PATH"
4. Restart your terminal/command prompt

### Verify Installation
```bash
gcloud --version
```

### Authenticate with Google Cloud
```bash
gcloud auth login
```
This will open a browser window - sign in with your Google account.

## Phase 3: Set Up Your Project

### 1. Set Your Project
```bash
# Replace with your actual project ID
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs
```bash
# Enable Cloud Run
gcloud services enable run.googleapis.com

# Enable Cloud Build (for building containers)
gcloud services enable cloudbuild.googleapis.com

# Enable Container Registry (for storing Docker images)
gcloud services enable containerregistry.googleapis.com
```

### 3. Verify Setup
```bash
# Check your project
gcloud config get-value project

# Check enabled services
gcloud services list --enabled | grep -E "(run|cloudbuild|containerregistry)"
```

## Phase 4: Deploy Your Backend

### Option A: One-Command Deploy (Recommended)
```bash
cd backend
gcloud run deploy documind-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### Option B: Using Our Scripts
- **Windows**: Double-click `deploy-to-cloud-run.bat`
- **Linux/Mac**: Run `./deploy-to-cloud-run.sh`

## Phase 5: Set Environment Variables (Optional)

### Add Redis Credentials
```bash
gcloud run services update documind-backend \
  --region us-central1 \
  --set-env-vars REDIS_HOST="your-redis-host" \
  --set-env-vars REDIS_PASSWORD="your-redis-password"
```

### Add Other Environment Variables
```bash
gcloud run services update documind-backend \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY="your-openai-key" \
  --set-env-vars SENTENCE_TRANSFORMERS_HOME="/tmp"
```

## Phase 6: Test Your Deployment

### Get Your Service URL
```bash
gcloud run services describe documind-backend \
  --region us-central1 \
  --format "value(status.url)"
```

### Test the API
```bash
# Replace with your actual URL
curl https://YOUR_URL.a.run.app/health
curl https://YOUR_URL.a.run.app/api/stats
```

## Phase 7: Update Frontend

### Update Frontend Environment
Once your backend is deployed, update your frontend `.env.production`:
```
REACT_APP_API_URL=https://YOUR_URL.a.run.app
```

## 🎯 Quick Checklist

- [ ] Google Cloud account created
- [ ] Billing set up
- [ ] Project created (remember Project ID!)
- [ ] Google Cloud CLI installed
- [ ] Authenticated with `gcloud auth login`
- [ ] Project set with `gcloud config set project`
- [ ] Required APIs enabled
- [ ] Backend deployed
- [ ] Frontend updated with new API URL

## 💰 Cost Expectations

**Google Cloud Run Free Tier (per month):**
- 2 million requests
- 1GB outbound data
- 360,000 GB-seconds compute time
- **Most projects stay within free tier!**

**If you exceed free tier:**
- ~$0.40 per million requests
- ~$0.12 per GB data transfer
- ~$0.000024 per GB-second compute time

## 🆘 Troubleshooting

### Common Issues
1. **"Project not found"**: Check your project ID with `gcloud config get-value project`
2. **"Billing required"**: Set up billing in Google Cloud Console
3. **"Permission denied"**: Make sure you're logged in: `gcloud auth login`
4. **Build fails**: Check logs with `gcloud run logs tail documind-backend --region us-central1`

### Get Help
- Check deployment logs: `gcloud run logs read documind-backend --region us-central1`
- Check service status: `gcloud run services describe documind-backend --region us-central1`

## 🚀 Ready to Start?

1. Go to https://console.cloud.google.com
2. Create your project
3. Install Google Cloud CLI
4. Run the deployment commands above!

**Estimated time**: 15-20 minutes for complete setup
