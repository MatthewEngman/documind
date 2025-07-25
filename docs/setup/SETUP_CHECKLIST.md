# 🎯 Google Cloud Setup Checklist

## Step 1: Create Google Cloud Account (5 minutes)
- [ ] Go to https://console.cloud.google.com
- [ ] Sign in with Google account
- [ ] Accept terms (get $300 free credits!)

## Step 2: Create Project (2 minutes)
- [ ] Click "Select a project" → "New Project"
- [ ] Project name: `documind-backend`
- [ ] **Write down your Project ID** (you'll need it!)

## Step 3: Set Up Billing (3 minutes)
- [ ] Go to Billing in left sidebar
- [ ] Add payment method
- [ ] **Note**: Free tier covers most usage!

## Step 4: Install Google Cloud CLI (5 minutes)
- [ ] Download: https://cloud.google.com/sdk/docs/install
- [ ] Run installer
- [ ] Restart terminal

## Step 5: Authenticate (1 minute)
```bash
gcloud auth login
```

## Step 6: Set Project (1 minute)
```bash
gcloud config set project YOUR_PROJECT_ID
```

## Step 7: Enable APIs (1 minute)
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Step 8: Deploy (2 minutes)
```bash
cd backend
gcloud run deploy documind-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## ✅ Total Time: ~20 minutes

## 🆘 Need Help?
- **Stuck?** Check `GOOGLE_CLOUD_SETUP.md` for detailed instructions
- **Error?** Run: `gcloud run logs tail documind-backend --region us-central1`
- **Questions?** Check the troubleshooting section in `GOOGLE_CLOUD_SETUP.md`

## 🎯 Your Action Items
1. **Start with Step 1** - Go to https://console.cloud.google.com
2. **Follow the checklist** - Cross off each item as you complete it
3. **Deploy your backend** - Use the commands above

**Ready to begin?** Start with creating your Google Cloud account at https://console.cloud.google.com!
