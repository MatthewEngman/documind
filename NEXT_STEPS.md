# 🎯 After CLI Setup - Next Steps

## ✅ You're Almost There!

Your CLI setup script is running the Google Cloud CLI installation and authentication. Here's what happens next:

## Phase 1: Complete Setup (Running Now)
- ✅ Google Cloud CLI installation
- ✅ Authentication
- ✅ Project creation/setup
- ✅ Service enablement
- ✅ Billing setup guidance

## Phase 2: Deploy Your Backend (2 minutes)

### Option A: One-Command Deploy
After the setup script finishes, run:
```bash
cd backend
gcloud run deploy documind-backend --source . --region us-central1 --platform managed --allow-unauthenticated
```

### Option B: Using Our Script
```bash
# Windows
.\deploy-to-cloud-run.bat

# Mac/Linux  
./deploy-to-cloud-run.sh
```

## Phase 3: Set Environment Variables (Optional)

### Add Redis Credentials
```bash
gcloud run services update documind-backend --region us-central1 --set-env-vars REDIS_HOST="your-redis-host" --set-env-vars REDIS_PASSWORD="your-redis-password"
```

### Add OpenAI API Key (if needed)
```bash
gcloud run services update documind-backend --region us-central1 --set-env-vars OPENAI_API_KEY="your-openai-key"
```

## Phase 4: Get Your API URL
```bash
gcloud run services describe documind-backend --region us-central1 --format "value(status.url)"
```

## Phase 5: Test Your Deployment
```bash
# Replace with your actual URL
curl https://YOUR_URL.a.run.app/health
curl https://YOUR_URL.a.run.app/api/stats
```

## Phase 6: Update Frontend
Update your frontend `.env.production`:
```
REACT_APP_API_URL=https://YOUR_URL.a.run.app
```

## 🎯 Quick Commands Reference

### Check Status
```bash
gcloud config get-value project
gcloud run services list --region us-central1
gcloud run services describe documind-backend --region us-central1
```

### View Logs
```bash
gcloud run logs tail documind-backend --region us-central1
```

### Update Environment
```bash
gcloud run services update documind-backend --region us-central1 --set-env-vars KEY="value"
```

## 🆘 If You Get Stuck

### Common Commands
```bash
# Check authentication
gcloud auth list

# Check project
gcloud config get-value project

# List services
gcloud run services list --region us-central1

# View logs
gcloud run logs read documind-backend --region us-central1
```

## 🚀 Ready to Deploy?

1. **Wait** for the setup script to finish
2. **Run** the deployment command above
3. **Get** your API URL
4. **Test** your deployment
5. **Update** your frontend

**Your backend will be live in under 5 minutes!** 🎉

## 💡 Pro Tips
- **Free tier**: 2M requests/month included
- **Auto-scaling**: Scales to zero when not used
- **SSL**: Automatic HTTPS certificates
- **Global**: Available worldwide

**Estimated total time: 10-15 minutes from start to finish!**
