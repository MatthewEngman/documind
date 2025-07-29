#!/usr/bin/env python3
"""Test script to verify all imports work correctly after fixes"""

try:
    from app.services.document_processor import document_processor
    print("✅ DocumentProcessor imports successfully")
except Exception as e:
    print(f"❌ DocumentProcessor import failed: {e}")

try:
    from app.services.vector_search_service import vector_search_service
    print("✅ VectorSearchService imports successfully")
except Exception as e:
    print(f"❌ VectorSearchService import failed: {e}")

try:
    from app.database.redis_client import redis_client
    print("✅ RedisClient imports successfully")
except Exception as e:
    print(f"❌ RedisClient import failed: {e}")

print("Import test completed")
