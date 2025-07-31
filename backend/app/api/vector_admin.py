"""
Vector administration endpoints for debugging and maintenance
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.database.redis_client import redis_client
from app.services.vector_search_service import VectorSearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vector-admin", tags=["vector-admin"])

@router.post("/reset-vector-index")
async def reset_vector_index() -> Dict[str, Any]:
    """
    Reset the vector index to fix serialization format issues
    WARNING: This will delete all existing vectors and require re-indexing
    """
    try:
        if not redis_client.client:
            raise HTTPException(status_code=500, detail="Redis client not available")
        
        vector_service = VectorSearchService()
        index_name = vector_service.vector_index_name
        
        # Step 1: Drop existing index if it exists
        try:
            redis_client.client.ft(index_name).dropindex(delete_documents=True)
            logger.info(f"Dropped existing vector index: {index_name}")
            dropped_existing = True
        except Exception as e:
            logger.info(f"No existing index to drop: {e}")
            dropped_existing = False
        
        # Step 2: Delete all vector keys to clean up any corrupted data
        vector_keys = []
        try:
            # Find all vector keys
            for key in redis_client.client.scan_iter(match="vector:*"):
                vector_keys.append(key.decode() if isinstance(key, bytes) else key)
            
            # Delete them
            if vector_keys:
                redis_client.client.delete(*vector_keys)
                logger.info(f"Deleted {len(vector_keys)} vector keys")
        except Exception as e:
            logger.error(f"Error cleaning vector keys: {e}")
        
        # Step 3: Recreate the index with correct schema
        await vector_service.initialize_vector_index()
        logger.info(f"Recreated vector index: {index_name}")
        
        # Step 4: Get stats
        try:
            index_info = redis_client.client.ft(index_name).info()
            index_exists = True
        except Exception:
            index_exists = False
        
        return {
            "success": True,
            "message": "Vector index reset successfully",
            "details": {
                "dropped_existing_index": dropped_existing,
                "deleted_vector_keys": len(vector_keys),
                "new_index_created": index_exists,
                "index_name": index_name
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to reset vector index: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset vector index: {str(e)}")

@router.get("/vector-index-info")
async def get_vector_index_info() -> Dict[str, Any]:
    """Get information about the current vector index"""
    try:
        if not redis_client.client:
            raise HTTPException(status_code=500, detail="Redis client not available")
        
        vector_service = VectorSearchService()
        index_name = vector_service.vector_index_name
        
        # Get index info
        try:
            index_info = redis_client.client.ft(index_name).info()
            index_exists = True
            
            # Convert bytes to strings for JSON serialization
            info_dict = {}
            for key, value in index_info.items():
                if isinstance(key, bytes):
                    key = key.decode()
                if isinstance(value, bytes):
                    value = value.decode()
                info_dict[key] = value
                
        except Exception as e:
            index_exists = False
            info_dict = {"error": str(e)}
        
        # Count vector keys
        vector_count = 0
        try:
            for _ in redis_client.client.scan_iter(match="vector:*"):
                vector_count += 1
        except Exception as e:
            logger.error(f"Error counting vectors: {e}")
        
        return {
            "index_name": index_name,
            "index_exists": index_exists,
            "index_info": info_dict,
            "vector_count": vector_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get vector index info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get index info: {str(e)}")

@router.post("/test-vector-serialization")
async def test_vector_serialization() -> Dict[str, Any]:
    """Test vector serialization methods to debug UTF-8 issues"""
    try:
        vector_service = VectorSearchService()
        
        # Test vector
        test_vector = [0.1, 0.2, 0.3, -0.4, 0.5]
        
        # Test serialization
        serialized = vector_service._serialize_vector(test_vector)
        deserialized = vector_service._deserialize_vector(serialized)
        
        # Test with different formats
        import struct
        import numpy as np
        
        # Old format
        old_bytes = struct.pack(f'{len(test_vector)}f', *test_vector)
        old_deserialized = vector_service._deserialize_vector(old_bytes)
        
        # New format  
        new_bytes = np.array(test_vector, dtype=np.float32).tobytes()
        new_deserialized = vector_service._deserialize_vector(new_bytes)
        
        return {
            "success": True,
            "test_vector": test_vector,
            "current_method": {
                "serialized_length": len(serialized),
                "serialized_hex": serialized.hex(),
                "deserialized": deserialized,
                "round_trip_success": np.allclose(deserialized, test_vector)
            },
            "old_format_compatibility": {
                "serialized_length": len(old_bytes),
                "serialized_hex": old_bytes.hex(),
                "deserialized": old_deserialized,
                "compatibility_success": old_deserialized == test_vector
            },
            "new_format_compatibility": {
                "serialized_length": len(new_bytes),
                "serialized_hex": new_bytes.hex(),
                "deserialized": new_deserialized,
                "compatibility_success": np.allclose(new_deserialized, test_vector)
            }
        }
        
    except Exception as e:
        logger.error(f"Vector serialization test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
