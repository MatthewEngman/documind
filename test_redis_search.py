#!/usr/bin/env python3
"""
Test Redis Stack search specifically to isolate the UTF-8 decode error
"""
import sys
import os
import numpy as np
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_redis_search_directly():
    """Test Redis Stack search directly to isolate the UTF-8 error"""
    print("🔍 Testing Redis Stack Search Directly")
    print("=" * 50)
    
    try:
        from app.database.redis_client import redis_client
        from redis.commands.search.query import Query
        
        if not redis_client.client:
            print("❌ Redis client not available")
            return
            
        print("✅ Redis client connected")
        
        # Test vector
        test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
        
        # Test both serialization methods
        print("\n📦 Testing Serialization Methods:")
        
        # Method 1: numpy (NEW)
        numpy_bytes = np.array(test_vector, dtype=np.float32).tobytes()
        print(f"Numpy bytes: {len(numpy_bytes)} bytes, hex: {numpy_bytes.hex()}")
        
        # Method 2: struct (OLD) 
        import struct
        struct_bytes = struct.pack(f'{len(test_vector)}f', *test_vector)
        print(f"Struct bytes: {len(struct_bytes)} bytes, hex: {struct_bytes.hex()}")
        
        # Test Redis Stack search with both formats
        index_name = "doc_vectors"
        limit = 5
        
        print(f"\n🔍 Testing Redis Stack Search:")
        
        for method_name, vector_bytes in [("numpy", numpy_bytes), ("struct", struct_bytes)]:
            print(f"\nTesting {method_name} format:")
            try:
                # Build query exactly like our code
                q = Query(f"*=>[KNN {limit} @vector $vector AS vector_score]").dialect(2)
                
                print(f"  Query: {q}")
                print(f"  Vector bytes length: {len(vector_bytes)}")
                print(f"  First 10 bytes: {vector_bytes[:10]}")
                
                # Execute search
                results = redis_client.client.ft(index_name).search(
                    q,
                    query_params={"vector": vector_bytes}
                )
                
                print(f"  ✅ Search successful: {len(results.docs)} results")
                
            except Exception as e:
                print(f"  ❌ Search failed: {e}")
                print(f"  Error type: {type(e).__name__}")
                
                # Check if it's specifically a UTF-8 decode error
                if "utf-8" in str(e).lower() and "decode" in str(e).lower():
                    print(f"  🚨 This is the UTF-8 decode error we're seeing!")
                    
                    # Try to understand where it's coming from
                    print(f"  Analyzing error location...")
                    import traceback
                    traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()

async def test_vector_service_methods():
    """Test our VectorSearchService methods directly"""
    print(f"\n🔧 Testing VectorSearchService Methods")
    print("=" * 50)
    
    try:
        from app.services.vector_search_service import VectorSearchService
        
        service = VectorSearchService()
        test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
        
        print("Testing _serialize_vector:")
        try:
            serialized = service._serialize_vector(test_vector)
            print(f"  ✅ Success: {len(serialized)} bytes")
            print(f"  Hex: {serialized.hex()}")
            
            print("Testing _deserialize_vector:")
            deserialized = service._deserialize_vector(serialized)
            print(f"  ✅ Success: {deserialized}")
            print(f"  Match: {np.allclose(deserialized, test_vector)}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Failed to import VectorSearchService: {e}")

async def main():
    print("🚀 Redis Search Specific Debug Script")
    print("=" * 60)
    
    await test_redis_search_directly()
    await test_vector_service_methods()
    
    print(f"\n🏁 Redis search debug completed!")

if __name__ == "__main__":
    asyncio.run(main())
