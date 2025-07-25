@echo off
setlocal enabledelayedexpansion

echo ======================================
echo 🚀 Google Cloud CLI Setup for DocuMind
echo ======================================

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Google Cloud CLI not found.
    echo 📥 Installing Google Cloud SDK...
    
    REM Download and install Google Cloud SDK
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe', '%TEMP%\GoogleCloudSDKInstaller.exe')"
    echo 🔄 Please run the installer that just opened...
    start %TEMP%\GoogleCloudSDKInstaller.exe
    echo ✅ After installation, restart this script
    pause
    exit /b 1
)

echo ✅ Google Cloud CLI is installed!

REM Authenticate
echo 🔐 Checking authentication...
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 Not authenticated. Running authentication...
    gcloud auth login
)

echo ✅ Authentication complete!

REM Check/set project
echo 📋 Checking project...
for /f "tokens=*" %%i in ('gcloud config get-value project') do set CURRENT_PROJECT=%%i
if "%CURRENT_PROJECT%"=="" (
    echo 📁 No project set. Creating new project...
    set /p PROJECT_ID="Enter project ID (e.g., documind-backend-2024): "
    gcloud projects create %PROJECT_ID%
    gcloud config set project %PROJECT_ID%
    echo ✅ Project %PROJECT_ID% created!
) else (
    echo ✅ Using project: %CURRENT_PROJECT%
    set PROJECT_ID=%CURRENT_PROJECT%
)

REM Enable required services
echo 🔧 Enabling required services...
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
echo ✅ Services enabled!

REM Check billing
echo 💳 Checking billing setup...
gcloud billing projects describe %PROJECT_ID% >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Billing not set up. Please set up billing:
    echo    https://console.cloud.google.com/billing/linkedaccount?project=%PROJECT_ID%
    echo.
    echo 🔄 After setting up billing, press any key to continue...
    pause
)

echo.
echo ======================================
echo 🎯 Ready to deploy!
echo ======================================
echo.
echo 🚀 Deploy your backend with:
echo    cd backend
echo    gcloud run deploy documind-backend --source . --region us-central1 --platform managed --allow-unauthenticated
echo.
echo 📋 Or run our automated script:
echo    deploy-to-cloud-run.bat
echo.
echo 🔗 After deployment, your API will be at:
echo    https://YOUR_URL.a.run.app
echo.
echo 🧪 Test with:
echo    curl https://YOUR_URL.a.run.app/health
echo.
pause
