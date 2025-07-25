@echo off
echo Deploying DocuMind Frontend to Vercel...
echo.
echo Project: documind-redis-challenge
echo Backend: https://documind-backend-700575219498.us-central1.run.app
echo.
npx vercel --prod --yes --name documind-redis-challenge
