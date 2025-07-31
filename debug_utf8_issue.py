#!/usr/bin/env python3
"""
Focused debug script to understand the UTF-8 decode issue
"""
import sys
import os
import numpy as np
import struct

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def analyze_utf8_decode_error():
    """Analyze the specific UTF-8 decode error we're seeing"""
    print("🔍 Analyzing UTF-8 Decode Error")
    print("=" * 40)
    
    # Create test vector
    test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
    print(f"Test vector: {test_vector}")
    
    # Method 1: struct.pack (OLD format)
    old_bytes = struct.pack(f'{len(test_vector)}f', *test_vector)
    print(f"\nOLD format (struct.pack):")
    print(f"  Bytes length: {len(old_bytes)}")
    print(f"  First 10 bytes: {old_bytes[:10]}")
    print(f"  Hex representation: {old_bytes.hex()}")
    print(f"  Byte at position 0: 0x{old_bytes[0]:02x} (decimal: {old_bytes[0]})")
    
    # Method 2: numpy.tobytes (NEW format)  
    new_bytes = np.array(test_vector, dtype=np.float32).tobytes()
    print(f"\nNEW format (numpy.tobytes):")
    print(f"  Bytes length: {len(new_bytes)}")
    print(f"  First 10 bytes: {new_bytes[:10]}")
    print(f"  Hex representation: {new_bytes.hex()}")
    print(f"  Byte at position 0: 0x{new_bytes[0]:02x} (decimal: {new_bytes[0]})")
    
    # Check if 0x9c appears in either format
    print(f"\nLooking for problematic byte 0x9c (decimal 156):")
    print(f"  In OLD format: {'YES' if 0x9c in old_bytes else 'NO'}")
    print(f"  In NEW format: {'YES' if 0x9c in new_bytes else 'NO'}")
    
    # Test cross-compatibility
    print(f"\n🔄 Cross-Compatibility Test:")
    
    # Try numpy.frombuffer on old bytes
    print("  numpy.frombuffer on OLD bytes:")
    try:
        result = np.frombuffer(old_bytes, dtype=np.float32).tolist()
        print(f"    ✅ Success: {result}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Try struct.unpack on new bytes
    print("  struct.unpack on NEW bytes:")
    try:
        num_floats = len(new_bytes) // 4
        result = list(struct.unpack(f'{num_floats}f', new_bytes))
        print(f"    ✅ Success: {result}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_specific_error_byte():
    """Test with the specific byte that's causing the error"""
    print(f"\n🚨 Testing Specific Error Byte (0x9c)")
    print("=" * 40)
    
    # Create a byte sequence that starts with 0x9c
    problematic_bytes = bytes([0x9c, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04])
    print(f"Problematic bytes: {problematic_bytes}")
    print(f"Hex: {problematic_bytes.hex()}")
    
    # Try to decode with numpy
    print("Trying numpy.frombuffer:")
    try:
        result = np.frombuffer(problematic_bytes, dtype=np.float32)
        print(f"  ✅ Success: {result}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Try to decode with struct
    print("Trying struct.unpack:")
    try:
        num_floats = len(problematic_bytes) // 4
        result = list(struct.unpack(f'{num_floats}f', problematic_bytes))
        print(f"  ✅ Success: {result}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def simulate_redis_vector_search_error():
    """Simulate the exact error we're seeing in Redis vector search"""
    print(f"\n🔍 Simulating Redis Vector Search Error")
    print("=" * 40)
    
    try:
        from app.services.vector_search_service import VectorSearchService
        
        # Create service instance
        service = VectorSearchService()
        
        # Test serialization methods
        test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
        
        print("Testing current serialization method:")
        try:
            serialized = service._serialize_vector(test_vector)
            print(f"  ✅ Serialization success: {len(serialized)} bytes")
            print(f"  First 10 bytes: {serialized[:10]}")
            print(f"  Hex: {serialized.hex()}")
            
            # Test deserialization
            deserialized = service._deserialize_vector(serialized)
            print(f"  ✅ Deserialization success: {deserialized}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            
    except Exception as e:
        print(f"❌ Failed to import VectorSearchService: {e}")

if __name__ == "__main__":
    print("🚀 UTF-8 Decode Error Debug Script")
    print("=" * 50)
    
    analyze_utf8_decode_error()
    test_specific_error_byte()
    simulate_redis_vector_search_error()
    
    print(f"\n🏁 Debug completed!")
