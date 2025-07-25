# Google Cloud Run Deployment Guide

## Overview
This guide explains how to deploy the documind FastAPI backend to Google Cloud Run, which is simpler and more reliable than Railway's nixpacks configuration.

## Prerequisites
1. **Google Cloud Project** - Create or select a project
2. **Google Cloud CLI** - Install and authenticate with `gcloud auth login`
3. **Enable APIs** - Cloud Run API and Cloud Build API
4. **Docker** - For local testing (optional)

## Quick Deployment Steps

### 1. Set up Google Cloud Project
```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Deploy from Local Machine
```bash
# Navigate to backend directory
cd backend

# Deploy to Cloud Run (builds and deploys in one command)
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

### 3. Set Environment Variables (if needed)
```bash
# Set Redis credentials
gcloud run services update documind-backend \
  --region us-central1 \
  --set-env-vars REDIS_HOST="your-redis-host" \
  --set-env-vars REDIS_PASSWORD="your-redis-password"
```

## Alternative: CI/CD with Cloud Build

### 1. Connect Repository to Cloud Build
- Go to Cloud Build in Google Cloud Console
- Connect your GitHub repository
- Create a trigger for the `backend/` directory

### 2. Automatic Deployment
The `cloudbuild.yaml` file will automatically:
- Build the Docker image
- Push to Container Registry
- Deploy to Cloud Run

## Local Testing
```bash
# Build Docker image locally
docker build -t documind-backend .

# Run locally
docker run -p 8080:8080 documind-backend

# Test the API
curl http://localhost:8080/health
```

## Advantages over Railway
- **Simple Dockerfile** - No nixpacks configuration needed
- **Better monorepo support** - Clear build context
- **Reliable builds** - Standard Docker workflow
- **Easy environment variables** - Simple CLI commands
- **Auto-scaling** - Built-in traffic-based scaling
- **Cost-effective** - Pay only for requests

## Configuration Files
- `Dockerfile` - Container build instructions
- `cloudbuild.yaml` - CI/CD pipeline (optional)
- `.dockerignore` - Files to exclude from build context

## Troubleshooting
- **Build fails**: Check Dockerfile and requirements.txt
- **App crashes**: Check logs with `gcloud run logs tail documind-backend --region us-central1`
- **Environment issues**: Verify environment variables are set correctly

The Cloud Run deployment is much simpler than Railway's nixpacks approach and should resolve all the configuration issues we've been experiencing.
