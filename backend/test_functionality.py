#!/usr/bin/env python3
"""Test script to verify core functionality works after fixes"""

import asyncio
import json
from app.services.document_processor import document_processor
from app.services.vector_search_service import vector_search_service
from app.database.redis_client import redis_client

async def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")
    try:
        health = redis_client.health_check()
        print(f"✅ Redis health check: {health}")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_document_processing():
    """Test document processing pipeline"""
    print("\n🔍 Testing document processing...")
    try:
        test_content = b"This is a test document for DocuMind. It contains sample text to verify the processing pipeline works correctly."
        
        result = await document_processor.process_document(
            file_content=test_content,
            filename="test_document.txt"
        )
        
        print(f"✅ Document processing result: {json.dumps(result, indent=2)}")
        return result.get("doc_id")
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return None

async def test_vector_search(doc_id=None):
    """Test vector search functionality"""
    print("\n🔍 Testing vector search...")
    try:
        await vector_search_service.initialize_vector_index()
        
        results = await vector_search_service.search_vectors(
            query="test document sample text",
            limit=5
        )
        
        print(f"✅ Vector search results: {len(results)} found")
        for i, result in enumerate(results[:2]):
            print(f"  Result {i+1}: {result.get('content', '')[:50]}...")
        
        return len(results) > 0
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return False

async def test_document_deletion(doc_id):
    """Test document deletion"""
    if not doc_id:
        print("\n⚠️ Skipping deletion test - no doc_id")
        return True
        
    print(f"\n🔍 Testing document deletion for {doc_id}...")
    try:
        vector_deleted = await vector_search_service.delete_document_vectors(doc_id)
        
        # Delete document
        doc_deleted = await document_processor.delete_document(doc_id)
        
        print(f"✅ Document deletion: vectors={vector_deleted}, doc={doc_deleted}")
        return doc_deleted
    except Exception as e:
        print(f"❌ Document deletion failed: {e}")
        return False

async def main():
    """Run all functionality tests"""
    print("🚀 Starting DocuMind functionality tests...\n")
    
    redis_ok = await test_redis_connection()
    
    doc_id = await test_document_processing()
    
    search_ok = await test_vector_search(doc_id)
    
    delete_ok = await test_document_deletion(doc_id)
    
    print(f"\n📊 Test Summary:")
    print(f"  Redis Connection: {'✅' if redis_ok else '❌'}")
    print(f"  Document Processing: {'✅' if doc_id else '❌'}")
    print(f"  Vector Search: {'✅' if search_ok else '❌'}")
    print(f"  Document Deletion: {'✅' if delete_ok else '❌'}")
    
    all_passed = redis_ok and doc_id and search_ok and delete_ok
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
