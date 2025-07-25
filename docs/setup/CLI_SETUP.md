# Complete CLI Google Cloud Setup

## 🖥️ 100% Terminal-Based Google Cloud Setup

This guide uses only CLI commands - no web interface required!

## Phase 1: Install Google Cloud CLI

### Windows (PowerShell - Run as Administrator)
```powershell
# Download and install Google Cloud SDK
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:TEMP\GoogleCloudSDKInstaller.exe")
Start-Process "$env:TEMP\GoogleCloudSDKInstaller.exe" -Wait

# Restart PowerShell and verify
gcloud --version
```

### Mac (Terminal)
```bash
# Install via Homebrew
brew install --cask google-cloud-sdk

# Or install directly
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud --version
```

### Linux (Terminal)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install google-cloud-cli

# Or install script
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud --version
```

## Phase 2: Authenticate (Browser Required Once)
```bash
# This opens browser for authentication
gcloud auth login

# Verify authentication
gcloud auth list
```

## Phase 3: Create Project via CLI

### Option A: Interactive Project Creation
```bash
# Create new project (interactive)
gcloud projects create documind-backend-2024 \
  --name="DocuMind Backend" \
  --set-as-default

# Note: You'll need to set up billing via web interface
# This is the only step that requires web browser
```

### Option B: Use Existing Project
```bash
# List existing projects
gcloud projects list

# Set existing project
gcloud config set project YOUR_EXISTING_PROJECT_ID
```

## Phase 4: Complete Setup via CLI

### Enable All Required Services
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbilling.googleapis.com
```

### Set Up Billing (CLI Commands)
```bash
# List billing accounts
gcloud billing accounts list

# Link project to billing account
gcloud billing projects link YOUR_PROJECT_ID \
  --billing-account=BILLING_ACCOUNT_ID

# Verify billing is set up
gcloud billing projects describe YOUR_PROJECT_ID
```

## Phase 5: Deploy Backend (Pure CLI)

### One-Command Deployment
```bash
# Navigate to backend directory
cd backend

# Deploy to Cloud Run
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
```

### Set Environment Variables via CLI
```bash
# Add Redis credentials
gcloud run services update documind-backend \
  --region us-central1 \
  --set-env-vars REDIS_HOST="your-redis-host" \
  --set-env-vars REDIS_PASSWORD="your-redis-password"

# Add OpenAI API key
gcloud run services update documind-backend \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY="your-openai-key"
```

## Phase 6: Get Service URL (CLI)
```bash
# Get service URL
gcloud run services describe documind-backend \
  --region us-central1 \
  --format "value(status.url)"

# Test deployment
curl $(gcloud run services describe documind-backend --region us-central1 --format "value(status.url)")/health
```

## 🎯 Complete One-Liner Setup

### Windows PowerShell Script
```powershell
# Save this as setup-google-cloud.ps1
Write-Host "🚀 Starting Google Cloud CLI Setup..."

# Check if gcloud is installed
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Google Cloud SDK..."
    (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:TEMP\GoogleCloudSDKInstaller.exe")
    Start-Process "$env:TEMP\GoogleCloudSDKInstaller.exe" -Wait
}

# Authenticate
gcloud auth login

# Create project
$projectId = "documind-backend-$(Get-Random -Minimum 1000 -Maximum 9999)"
gcloud projects create $projectId --name="DocuMind Backend"
gcloud config set project $projectId

# Enable services
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

Write-Host "✅ Project created: $projectId"
Write-Host "💳 Next: Set up billing at https://console.cloud.google.com/billing"
```

### Bash Script (Mac/Linux)
```bash
#!/bin/bash
# Save this as setup-google-cloud.sh

echo "🚀 Starting Google Cloud CLI Setup..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Please install Google Cloud SDK first:"
    echo "Mac: brew install --cask google-cloud-sdk"
    echo "Linux: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Authenticate
gcloud auth login

# Create project
PROJECT_ID="documind-backend-$(date +%s)"
gcloud projects create $PROJECT_ID --name="DocuMind Backend"
gcloud config set project $PROJECT_ID

# Enable services
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo "✅ Project created: $PROJECT_ID"
echo "💳 Next: Set up billing at https://console.cloud.google.com/billing"
```

## 🎯 Quick Commands Reference

### Essential Commands
```bash
# Check current project
gcloud config get-value project

# List projects
gcloud projects list

# List services
gcloud services list --enabled

# Deploy backend
cd backend && gcloud run deploy documind-backend --source . --region us-central1 --platform managed --allow-unauthenticated

# View logs
gcloud run logs tail documind-backend --region us-central1

# Get service info
gcloud run services describe documind-backend --region us-central1
```

## 🆘 Troubleshooting CLI Issues

### Common CLI Commands
```bash
# Check authentication
gcloud auth list

# Update gcloud
gcloud components update

# Reset configuration
gcloud init

# Check billing
gcloud billing projects describe YOUR_PROJECT_ID
```

## ✅ CLI Setup Checklist

- [ ] Install Google Cloud CLI
- [ ] Run `gcloud auth login`
- [ ] Run `gcloud projects create` or set existing project
- [ ] Run `gcloud services enable` commands
- [ ] Set up billing (only web step required)
- [ ] Deploy with `gcloud run deploy`
- [ ] Test with `curl` commands

**Ready to start?** Open your terminal and begin with `gcloud auth login`!
