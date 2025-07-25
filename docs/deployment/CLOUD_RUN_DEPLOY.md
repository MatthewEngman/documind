# Google Cloud Run Deployment - Quick Start

## 🚀 One-Command Deployment

Your DocuMind backend is ready for Google Cloud Run deployment with all configuration files already in place!

### Prerequisites
1. **Google Cloud Account** - Sign up at https://cloud.google.com
2. **Google Cloud CLI** - Install from https://cloud.google.com/sdk/docs/install
3. **Billing enabled** - Set up billing for your project

### Quick Deploy (2 minutes)

#### Option 1: Windows (Double-click)
1. Double-click `deploy-to-cloud-run.bat`
2. Follow the prompts
3. Done!

#### Option 2: Linux/Mac/Terminal
```bash
./deploy-to-cloud-run.sh
```

#### Option 3: Manual Command
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

### Set Redis Environment Variables (Optional)
```bash
gcloud run services update documind-backend \
  --region us-central1 \
  --set-env-vars REDIS_HOST="your-redis-host" \
  --set-env-vars REDIS_PASSWORD="your-redis-password"
```

### Test Your Deployment
```bash
curl https://YOUR-URL-HERE.a.run.app/health
curl https://YOUR-URL-HERE.a.run.app/api/stats
```

### Frontend Configuration
Once your backend is deployed, update your frontend `.env.production`:
```
REACT_APP_API_URL=https://YOUR-URL-HERE.a.run.app
```

### ✅ What's Already Configured
- ✅ Dockerfile with Python 3.11
- ✅ Cloud Build configuration
- ✅ .dockerignore optimized
- ✅ Health check endpoints
- ✅ Automatic scaling
- ✅ SSL/TLS certificates
- ✅ CORS configuration

### 📊 Cost Estimate
- **Free tier**: 2 million requests/month
- **Typical usage**: ~$5-15/month for moderate traffic
- **Pay-per-use**: Only charged when requests are processed

### 🔧 Troubleshooting
- **Build fails**: Check `gcloud run logs tail documind-backend --region us-central1`
- **Authentication**: Run `gcloud auth login`
- **Project issues**: Run `gcloud config set project YOUR_PROJECT_ID`

### 🎯 Next Steps
1. Deploy backend with one of the options above
2. Update frontend environment variables
3. Deploy frontend to Vercel
4. Test end-to-end functionality

Your Cloud Run deployment is ready to go! 🚀
