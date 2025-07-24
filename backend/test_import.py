#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, '/home/ubuntu/repos/documind/backend')

try:
    print("Testing FastAPI app import...")
    from app.main import app
    print("✅ FastAPI app imported successfully!")
    print("✅ Railway deployment should work now")
    
    routes = [route.path for route in app.routes]
    print(f"Available routes: {routes}")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
