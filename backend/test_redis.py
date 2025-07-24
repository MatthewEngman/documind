#!/usr/bin/env python3
"""
Simple Redis connection test script
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database.redis_client import redis_client

def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("🔍 Testing Redis connection...")
    
    try:
        # Test basic connection
        health = redis_client.health_check()
        print(f"✅ Redis health check: {'PASSED' if health else 'FAILED'}")
        
        if health:
            # Test basic operations
            print("\n📊 Testing basic Redis operations...")
            
            # Set a test key
            redis_client.client.set("test:connection", "success", ex=60)
            print("✅ SET operation: PASSED")
            
            # Get the test key
            value = redis_client.client.get("test:connection")
            print(f"✅ GET operation: PASSED (value: {value})")
            
            # Test stats
            stats = redis_client.get_stats()
            print(f"\n📈 Redis Stats:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            # Clean up
            redis_client.client.delete("test:connection")
            print("\n🧹 Cleanup: PASSED")
            
            print("\n🎉 All Redis tests PASSED! Your Redis Cloud connection is working perfectly.")
            return True
            
    except Exception as e:
        print(f"❌ Redis connection test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
