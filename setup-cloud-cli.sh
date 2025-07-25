#!/bin/bash

# Google Cloud CLI Setup Script for DocuMind
# Run this to set up Google Cloud entirely via CLI

set -e

echo "======================================"
echo "🚀 Google Cloud CLI Setup for DocuMind"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found.${NC}"
    echo "📥 Please install Google Cloud SDK:"
    echo "  Mac: brew install --cask google-cloud-sdk"
    echo "  Ubuntu/Debian: sudo apt-get install google-cloud-cli"
    echo "  Or visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${GREEN}✅ Google Cloud CLI is installed!${NC}"

# Authenticate
echo -e "${YELLOW}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}🔐 Not authenticated. Running authentication...${NC}"
    gcloud auth login
fi

echo -e "${GREEN}✅ Authentication complete!${NC}"

# Check/set project
echo -e "${YELLOW}📋 Checking project...${NC}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo -e "${YELLOW}📁 No project set.${NC}"
    
    # List existing projects
    echo "📋 Existing projects:"
    gcloud projects list --format="table(projectId, name)"
    
    read -p "Create new project (y/n)? " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter project ID (e.g., documind-backend-2024): " PROJECT_ID
        echo -e "${YELLOW}📁 Creating project: $PROJECT_ID${NC}"
        gcloud projects create $PROJECT_ID
        gcloud config set project $PROJECT_ID
        echo -e "${GREEN}✅ Project $PROJECT_ID created!${NC}"
    else
        read -p "Enter existing project ID: " PROJECT_ID
        gcloud config set project $PROJECT_ID
        echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
    fi
else
    PROJECT_ID=$CURRENT_PROJECT
    echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
fi

# Enable required services
echo -e "${YELLOW}🔧 Enabling required services...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
echo -e "${GREEN}✅ Services enabled!${NC}"

# Check billing
echo -e "${YELLOW}💳 Checking billing setup...${NC}"
if ! gcloud billing projects describe $PROJECT_ID --format="value(billingEnabled)" | grep -q "true"; then
    echo -e "${YELLOW}⚠️  Billing not set up.${NC}"
    echo "🔗 Please set up billing:"
    echo "   https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    echo ""
    read -p "Press Enter after setting up billing..."
fi

# Final summary
echo ""
echo "======================================"
echo -e "${GREEN}🎯 Setup Complete!${NC}"
echo "======================================"
echo ""
echo "🚀 Deploy your backend with:"
echo "   cd backend"
echo "   gcloud run deploy documind-backend --source . --region us-central1 --platform managed --allow-unauthenticated"
echo ""
echo "📋 Or run our automated script:"
echo "   ./deploy-to-cloud-run.sh"
echo ""
echo "🔗 After deployment, your API will be at:"
echo "   https://YOUR_URL.a.run.app"
echo ""
echo "🧪 Test with:"
echo "   curl https://YOUR_URL.a.run.app/health"
echo ""

# Ask if they want to deploy now
read -p "Deploy now (y/n)? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚀 Starting deployment...${NC}"
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
fi
