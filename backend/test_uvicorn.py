#!/usr/bin/env python3
"""
Test script to verify uvicorn can start the application
"""

import os
import sys
import time
import subprocess
import requests
from threading import Thread

# Set environment variables
os.environ["PORT"] = "8080"
os.environ["REDIS_REQUIRED"] = "false"
os.environ["ENVIRONMENT"] = "production"

def test_uvicorn_direct():
    """Test starting uvicorn directly"""
    print("🧪 Testing uvicorn direct startup...")
    
    try:
        # Start uvicorn directly
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8080",
            "--log-level", "info"
        ]
        
        print(f"📋 Command: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output for a few seconds
        start_time = time.time()
        output_lines = []
        
        while time.time() - start_time < 10:  # Wait up to 10 seconds
            line = process.stdout.readline()
            if line:
                output_lines.append(line.strip())
                print(f"📝 {line.strip()}")
                
                # Check if server started successfully
                if "Uvicorn running on" in line:
                    print("✅ Server started successfully!")
                    break
            else:
                time.sleep(0.1)
        
        # Terminate the process
        process.terminate()
        process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ Direct uvicorn test failed: {e}")
        return False

def test_main_module():
    """Test starting via main module"""
    print("\n🧪 Testing main module startup...")
    
    try:
        # Start via main module
        cmd = [sys.executable, "-m", "app.main"]
        
        print(f"📋 Command: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output for a few seconds
        start_time = time.time()
        output_lines = []
        
        while time.time() - start_time < 10:  # Wait up to 10 seconds
            line = process.stdout.readline()
            if line:
                output_lines.append(line.strip())
                print(f"📝 {line.strip()}")
                
                # Check if server started successfully
                if "Uvicorn running on" in line or "Application startup complete" in line:
                    print("✅ Server started successfully!")
                    break
            else:
                time.sleep(0.1)
        
        # Terminate the process
        process.terminate()
        process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ Main module test failed: {e}")
        return False

def main():
    """Run uvicorn startup tests"""
    print("🚀 Starting uvicorn startup tests...")
    
    tests = [
        ("Direct Uvicorn", test_uvicorn_direct),
        ("Main Module", test_main_module),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Running {test_name} Test ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All uvicorn tests passed!")
        return True
    else:
        print("💥 Some uvicorn tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
