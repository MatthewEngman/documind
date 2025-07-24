# DocuMind Production Deployment Checklist

## 📋 Manual Steps Required for Deployment

### ✅ Pre-Deployment Setup (COMPLETED)
- [x] **Railway Configuration Created** - `backend/railway.json`
- [x] **Railway Configuration Updated** - Switched from `nixpacks.toml` to `railway.toml` for better Railway compatibility
- [x] **Vercel Configuration Created** - `documind-frontend/vercel.json`
- [x] **Production Environment File Created** - `documind-frontend/.env.production`
- [x] **CORS Configuration Updated** - Production-ready CORS in `backend/app/main.py`
- [x] **Requirements.txt Updated** - Production dependencies aligned
- [x] **Package.json Updated** - Added `vercel-build` script
- [x] **Demo Script Created** - `DEMO_SCRIPT.md` for judges

---

## 🚀 Phase 1: Backend Deployment (Railway) - 15 minutes

### Manual Steps Required:

#### 1. Create Railway Account & Install CLI (5 min)
```bash
# 1. Go to https://railway.app and sign up with GitHub
# 2. Install Railway CLI
npm install -g @railway/cli

# 3. Login to Railway
railway login
```

#### 2. Initialize and Deploy Backend (5 min)
```bash
# Navigate to backend directory
cd backend

# Initialize Railway project
railway init

# Follow prompts:
# - Create new project? Yes
# - Project name: documind-api
# - Environment: production

# Deploy immediately
railway up
```

#### 3. Configure Environment Variables (5 min)
```bash
# Set environment variables via Railway CLI
railway variables set REDIS_HOST=your-redis-cloud-endpoint.com
railway variables set REDIS_PORT=12345
railway variables set REDIS_PASSWORD=your-redis-password
railway variables set REDIS_SSL=true
railway variables set OPENAI_API_KEY=your-openai-key

# Optional: Set other variables
railway variables set MAX_FILE_SIZE=10485760
railway variables set CACHE_TTL=3600
railway variables set DEBUG=false
```

#### 4. Get Backend URL and Test
```bash
# Get your Railway app URL
railway status

# Test your deployed backend
curl https://your-app-name.up.railway.app/health

# Expected response:
# {"status":"healthy","redis":"connected","version":"1.0.0"}
```

---

## 🎨 Phase 2: Frontend Deployment (Vercel) - 15 minutes

### Manual Steps Required:

#### 1. Update Environment Files (2 min)
**Update `documind-frontend/.env.production`:**
```bash
REACT_APP_API_URL=https://your-actual-railway-url.up.railway.app
REACT_APP_VERSION=1.0.0
```

**Update `documind-frontend/vercel.json`:**
```json
{
  "env": {
    "REACT_APP_API_URL": "https://your-actual-railway-url.up.railway.app"
  }
}
```

#### 2. Install Vercel CLI and Deploy (10 min)
```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd documind-frontend

# Install dependencies (if not done)
npm install

# Deploy to Vercel
vercel --prod

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: documind-redis-challenge
# - In which directory is your code? ./
# - Want to override settings? No
```

#### 3. Configure Environment Variables in Vercel (3 min)
```bash
# Add environment variables to Vercel
vercel env add REACT_APP_API_URL production
# Enter: https://your-app-name.up.railway.app

vercel env add REACT_APP_VERSION production  
# Enter: 1.0.0

# Redeploy with new environment variables
vercel --prod
```

---

## 🔗 Phase 3: Connect Everything (10 minutes)

### Manual Steps Required:

#### 1. Update Backend CORS for Frontend URL (5 min)
```bash
# Add your Vercel URL to Railway backend
railway variables set FRONTEND_URL=https://documind-redis-challenge.vercel.app

# Redeploy Railway app
railway up
```

#### 2. End-to-End Testing (5 min)
**Test Complete Flow:**
1. Visit your Vercel URL: `https://documind-redis-challenge.vercel.app`
2. Check that the interface loads properly
3. Upload a small text file
4. Verify the upload completes successfully
5. Try a search query
6. Check that results are returned
7. Visit the Analytics tab
8. Verify Redis metrics are showing

**Test API Endpoints Directly:**
```bash
# Health check
curl https://your-app-name.up.railway.app/health

# System stats
curl https://your-app-name.up.railway.app/api/system/stats

# Search analytics
curl https://your-app-name.up.railway.app/api/search/analytics
```

---

## 📝 Phase 4: Documentation & Submission (5 minutes)

### Manual Steps Required:

#### 1. Update README.md with Live URLs (3 min)
**Add to the top of README.md:**
```markdown
# DocuMind - Redis AI Challenge 2025 🏆

> **🌐 Live Demo:** https://documind-redis-challenge.vercel.app  
> **🔌 API Endpoint:** https://your-app-name.up.railway.app  
> **📊 Health Check:** https://your-app-name.up.railway.app/health
```

#### 2. Final Verification Checklist (2 min)
**✅ Pre-Submission Checklist:**
- [ ] Live demo URL loads and works
- [ ] Document upload functions end-to-end
- [ ] Search returns relevant results
- [ ] Analytics dashboard shows Redis metrics
- [ ] All HTTPS endpoints responding
- [ ] README.md has live demo links
- [ ] Demo script ready for judges
- [ ] Screenshots/videos as backup

---

## 🚨 Troubleshooting Guide

### Backend deployment fails:
```bash
railway logs  # Check deployment logs
railway shell # Debug in production environment
```

### Frontend deployment fails:
```bash
vercel logs  # Check build logs
vercel dev   # Test locally first
```

### CORS errors:
- Verify FRONTEND_URL is set in Railway
- Check allowed_origins in main.py
- Ensure HTTPS URLs (not HTTP)

### Redis connection issues:
- Verify Redis Cloud credentials
- Check Redis Cloud instance is running
- Test connection from Railway shell

---

## 🎯 Success Metrics

**Your URLs:**
- **🌐 Live Demo:** `https://documind-redis-challenge.vercel.app`
- **🔌 Backend API:** `https://your-app-name.up.railway.app`
- **📊 Health Check:** `https://your-app-name.up.railway.app/health`

**Performance Targets:**
- Search Speed: <100ms cached, <500ms uncached
- Memory Efficiency: 800+ documents in 30MB Redis Cloud free tier
- Cache Hit Rate: 60-85% typical performance
- Upload Processing: 5-10 seconds for multi-page PDFs

---

## 📋 Summary of Manual Actions Required

### Critical Manual Steps:
1. **Install CLI Tools** - Railway CLI and Vercel CLI
2. **Create Accounts** - Railway.app and Vercel accounts
3. **Deploy Backend** - Railway initialization and deployment
4. **Configure Environment Variables** - Redis credentials, API keys
5. **Deploy Frontend** - Vercel deployment and configuration
6. **Update URLs** - Replace placeholder URLs with actual deployment URLs
7. **Test End-to-End** - Verify complete functionality
8. **Update Documentation** - README with live demo links

### Estimated Total Time: 45 minutes

**All configuration files have been created and are ready for deployment!**
