# Railway Service Configuration Guide

## Important: Root Directory Configuration

Railway's config files (`railway.json`, `railway.toml`) **do not follow the Root Directory path** and require absolute paths. The root directory must be configured through Railway's service settings UI, not config files.

## Steps to Configure Railway Service Settings

1. **Access Railway Dashboard**
   - Go to your Railway project dashboard
   - Select the service you want to configure

2. **Configure Root Directory**
   - Click on the **Settings** tab
   - Find the **Root Directory** option
   - Set the root directory to: `backend`
   - This tells Railway to build and run from the `backend` subdirectory

3. **Verify Configuration**
   - The root directory setting should show: `backend`
   - Railway will now clone into this subdirectory when building your code

## Why This Is Required

Our project has a monorepo structure:
```
documind/
├── backend/           # FastAPI application
│   ├── app/
│   │   └── main.py   # Main application file
│   ├── requirements.txt
│   └── railway.json
├── documind-frontend/ # Frontend application
└── nixpacks.toml     # Build configuration
```

Railway needs to know that the Python application is in the `backend` directory, not the repository root. This ensures:
- Dependencies are installed from `backend/requirements.txt`
- The application starts from `backend/app/main.py`
- Build and runtime contexts are properly aligned

## Configuration Files

- **nixpacks.toml** (repository root): Handles build-time configuration
- **railway.toml** (repository root): Handles deployment-time configuration  
- **railway.json** (backend/): Service-specific settings (does NOT set root directory)

## Troubleshooting

If you see `ModuleNotFoundError: No module named 'fastapi'`:
1. Verify the root directory is set to `backend` in Railway's service settings UI
2. Check that Railway is building from the correct context
3. Ensure nixpacks is detecting the Python application automatically

The root directory setting in Railway's UI is the critical configuration that makes monorepo deployments work correctly.
