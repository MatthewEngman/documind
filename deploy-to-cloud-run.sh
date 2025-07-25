#!/bin/bash

# Google Cloud Run Deployment Script for DocuMind
# This script simplifies the deployment process for Google Cloud Run

set -e

echo "🚀 Starting DocuMind Cloud Run Deployment"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI (gcloud) is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
echo "🔍 Checking Google Cloud authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" || {
    echo "❌ Not authenticated with Google Cloud. Running authentication..."
    gcloud auth login
}

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project set. Please set a project:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Using project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy to Cloud Run
echo "📦 Building and deploying to Cloud Run..."
cd backend

gcloud run deploy documind-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars PORT=8080

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your API will be available at:"
echo "   https://documind-backend-XXXXXX-uc.a.run.app"
echo ""
echo "📊 Test your deployment:"
echo "   curl https://documind-backend-XXXXXX-uc.a.run.app/health"
echo ""
echo "📝 To set Redis environment variables, run:"
echo "   gcloud run services update documind-backend \\"
echo "     --region us-central1 \\"
echo "     --set-env-vars REDIS_HOST=your-redis-host \\"
echo "     --set-env-vars REDIS_PASSWORD=your-redis-password"
