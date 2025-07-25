@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting DocuMind Cloud Run Deployment

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Google Cloud CLI (gcloud) is not installed. Please install it first:
    echo    https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Check if user is authenticated
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Not authenticated with Google Cloud. Running authentication...
    gcloud auth login
)

REM Get project ID
for /f "tokens=*" %%i in ('gcloud config get-value project') do set PROJECT_ID=%%i
if "%PROJECT_ID%"=="" (
    echo ❌ No Google Cloud project set. Please set a project:
    echo    gcloud config set project YOUR_PROJECT_ID
    pause
    exit /b 1
)

echo ✅ Using project: %PROJECT_ID%

REM Enable required APIs
echo 🔧 Enabling required APIs...
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

REM Deploy to Cloud Run
echo 📦 Building and deploying to Cloud Run...
cd backend

gcloud run deploy documind-backend ^
  --source . ^
  --region us-central1 ^
  --platform managed ^
  --allow-unauthenticated ^
  --port 8080 ^^
  --memory 1Gi ^
  --cpu 1 ^
  --max-instances 10 ^
  --set-env-vars PORT=8080

echo ✅ Deployment complete!
echo.
echo 🌐 Your API will be available at:
echo    https://documind-backend-XXXXXX-uc.a.run.app
echo.
echo 📊 Test your deployment:
echo    curl https://documind-backend-XXXXXX-uc.a.run.app/health
echo.
echo 📝 To set Redis environment variables, run:
echo    gcloud run services update documind-backend ^
echo      --region us-central1 ^
echo      --set-env-vars REDIS_HOST=your-redis-host ^
echo      --set-env-vars REDIS_PASSWORD=your-redis-password
echo.
pause
