#!/usr/bin/env python3
"""
Test script to debug vector serialization/deserialization issues locally
"""
import sys
import os
import numpy as np
import struct
from typing import List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_vector_serialization():
    """Test both old and new vector serialization methods"""
    print("🔧 Testing Vector Serialization Methods")
    print("=" * 50)
    
    # Test vector
    test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
    print(f"Original vector: {test_vector}")
    print()
    
    # Method 1: Old struct.pack method
    print("📦 Method 1: struct.pack() (OLD)")
    try:
        old_bytes = struct.pack(f'{len(test_vector)}f', *test_vector)
        print(f"Serialized bytes length: {len(old_bytes)}")
        print(f"First few bytes: {old_bytes[:10]}")
        
        # Deserialize with old method
        num_floats = len(old_bytes) // 4
        old_deserialized = list(struct.unpack(f'{num_floats}f', old_bytes))
        print(f"Deserialized: {old_deserialized}")
        print(f"Match original: {old_deserialized == test_vector}")
        print()
    except Exception as e:
        print(f"❌ Old method failed: {e}")
        print()
    
    # Method 2: New numpy method
    print("🔢 Method 2: numpy.tobytes() (NEW)")
    try:
        new_bytes = np.array(test_vector, dtype=np.float32).tobytes()
        print(f"Serialized bytes length: {len(new_bytes)}")
        print(f"First few bytes: {new_bytes[:10]}")
        
        # Deserialize with new method
        new_deserialized = np.frombuffer(new_bytes, dtype=np.float32).tolist()
        print(f"Deserialized: {new_deserialized}")
        print(f"Match original: {np.allclose(new_deserialized, test_vector)}")
        print()
    except Exception as e:
        print(f"❌ New method failed: {e}")
        print()
    
    # Cross-compatibility test
    print("🔄 Cross-Compatibility Test")
    print("-" * 30)
    
    # Try to deserialize old format with new method
    print("Deserializing OLD bytes with NEW method:")
    try:
        cross_result = np.frombuffer(old_bytes, dtype=np.float32).tolist()
        print(f"Result: {cross_result}")
        print(f"Match: {np.allclose(cross_result, test_vector)}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Try to deserialize new format with old method
    print("Deserializing NEW bytes with OLD method:")
    try:
        num_floats = len(new_bytes) // 4
        cross_result2 = list(struct.unpack(f'{num_floats}f', new_bytes))
        print(f"Result: {cross_result2}")
        print(f"Match: {cross_result2 == test_vector}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()

def test_backward_compatible_deserializer():
    """Test our backward compatible deserializer"""
    print("🔧 Testing Backward Compatible Deserializer")
    print("=" * 50)
    
    def _deserialize_vector_compatible(vector_bytes: bytes) -> List[float]:
        """Our backward compatible deserializer"""
        try:
            # Try new numpy format first
            return np.frombuffer(vector_bytes, dtype=np.float32).tolist()
        except Exception as e1:
            print(f"Numpy method failed: {e1}")
            try:
                # Fallback to old struct format
                num_floats = len(vector_bytes) // 4
                return list(struct.unpack(f'{num_floats}f', vector_bytes))
            except Exception as e2:
                print(f"Struct method failed: {e2}")
                raise
    
    test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
    
    # Test with old format bytes
    old_bytes = struct.pack(f'{len(test_vector)}f', *test_vector)
    print("Testing with OLD format bytes:")
    try:
        result = _deserialize_vector_compatible(old_bytes)
        print(f"✅ Success: {result}")
        print(f"Match: {result == test_vector}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()
    
    # Test with new format bytes
    new_bytes = np.array(test_vector, dtype=np.float32).tobytes()
    print("Testing with NEW format bytes:")
    try:
        result = _deserialize_vector_compatible(new_bytes)
        print(f"✅ Success: {result}")
        print(f"Match: {np.allclose(result, test_vector)}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    print()

def test_redis_connection():
    """Test Redis connection and vector operations"""
    print("🔗 Testing Redis Connection")
    print("=" * 50)
    
    try:
        from app.database.redis_client import redis_client
        
        # Test connection
        if redis_client.client:
            print("✅ Redis client connected")
            
            # Test basic operations
            test_key = "test:vector:debug"
            test_data = {"test": "data"}
            
            redis_client.client.hset(test_key, mapping=test_data)
            retrieved = redis_client.client.hgetall(test_key)
            print(f"✅ Basic Redis operations working: {retrieved}")
            
            # Clean up
            redis_client.client.delete(test_key)
            
        else:
            print("❌ Redis client not available")
            
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
    print()

if __name__ == "__main__":
    print("🚀 Vector Serialization Debug Script")
    print("=" * 60)
    print()
    
    test_vector_serialization()
    test_backward_compatible_deserializer()
    test_redis_connection()
    
    print("🏁 Debug script completed!")
