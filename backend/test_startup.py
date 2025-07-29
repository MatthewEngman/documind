#!/usr/bin/env python3
"""
Test script to verify the application can start properly
This helps identify startup issues before deploying to Cloud Run
"""

import os
import sys

# Set environment variables FIRST before any imports
os.environ["PORT"] = "8080"
os.environ["REDIS_REQUIRED"] = "false"
os.environ["ENVIRONMENT"] = "production"

# Now import logging and configure it
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all imports work correctly"""
    try:
        logger.info("Testing imports...")
        
        # Test FastAPI import
        from fastapi import FastAPI
        logger.info("✅ FastAPI import successful")
        
        # Test uvicorn import
        import uvicorn
        logger.info("✅ Uvicorn import successful")
        
        # Test Redis import
        import redis
        logger.info("✅ Redis import successful")
        
        # Test app config
        from app.config import settings
        logger.info(f"✅ Config loaded - Port: {settings.api_port}")
        
        # Test Redis client
        from app.database.redis_client import redis_client
        logger.info("✅ Redis client import successful")
        
        # Test main app
        from app.main import app
        logger.info("✅ Main app import successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test that the FastAPI app can be created"""
    try:
        logger.info("Testing app creation...")
        
        from app.main import app
        
        # Check if app is properly configured
        logger.info(f"✅ App title: {app.title}")
        logger.info(f"✅ App version: {app.version}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ App creation failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection (should work with mock client)"""
    try:
        logger.info("Testing Redis connection...")
        
        from app.database.redis_client import redis_client
        
        # Test health check
        health = redis_client.health_check()
        logger.info(f"✅ Redis health check: {health}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis connection test failed: {e}")
        return False

def main():
    """Run all startup tests"""
    logger.info("🚀 Starting DocuMind startup tests...")
    
    tests = [
        ("Import Tests", test_imports),
        ("App Creation", test_app_creation),
        ("Redis Connection", test_redis_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} PASSED")
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    logger.info(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! App should start successfully.")
        return True
    else:
        logger.error("💥 Some tests failed. Fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
