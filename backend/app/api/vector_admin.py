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

@router.post("/cleanup-broken-vectors")
async def cleanup_broken_vectors():
    """Remove broken vectors that cause UTF-8 decode errors"""
    try:
        result = await VectorSearchService().cleanup_broken_vectors()
        return {
            "message": "Broken vector cleanup completed",
            "removed_vectors": result["removed"],
            "kept_vectors": result["kept"],
            "total_processed": result["removed"] + result["kept"]
        }
        
    except Exception as e:
        logger.error(f"Vector cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vector cleanup failed: {str(e)}")

@router.post("/regenerate-vectors")
async def regenerate_vectors_for_existing_documents():
    """Regenerate vectors for all existing documents that don't have vectors"""
    try:
        from app.services.document_processor import document_processor
        
        # Get all documents
        documents = await document_processor.list_documents(limit=1000)
        
        if not documents:
            return {
                "message": "No documents found to regenerate vectors for",
                "processed_documents": 0,
                "vectors_generated": 0
            }
        
        processed_count = 0
        total_vectors = 0
        errors = []
        
        for doc in documents:
            try:
                doc_id = doc["id"]
                logger.info(f"Regenerating vectors for document {doc_id}: {doc['filename']}")
                
                # Get document chunks
                chunks_data = redis_client.get_json(f"doc:chunks:{doc_id}")
                if not chunks_data:
                    logger.warning(f"No chunks found for document {doc_id}")
                    continue
                
                # Get individual chunks
                chunks = []
                for chunk_id in chunks_data.get("chunks", []):
                    chunk = redis_client.get_json(f"doc:chunk:{chunk_id}")
                    if chunk:
                        chunks.append(chunk)
                
                if not chunks:
                    logger.warning(f"No valid chunks found for document {doc_id}")
                    continue
                
                # Generate vectors for this document
                vectors_added = await VectorSearchService().add_document_vectors(doc_id, chunks)
                logger.info(f"Generated {vectors_added} vectors for document {doc_id}")
                
                processed_count += 1
                total_vectors += vectors_added
                
            except Exception as doc_error:
                error_msg = f"Failed to regenerate vectors for {doc.get('filename', 'unknown')}: {doc_error}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            "message": "Vector regeneration completed",
            "processed_documents": processed_count,
            "vectors_generated": total_vectors,
            "total_documents": len(documents),
            "errors": errors[:5]  # Show first 5 errors
        }
        
    except Exception as e:
        logger.error(f"Vector regeneration error: {e}")
        raise HTTPException(status_code=500, detail=f"Vector regeneration failed: {str(e)}")

@router.post("/clear-all-data")
async def clear_all_data() -> Dict[str, Any]:
    """
    Clear ALL documents, vectors, and related data for a complete fresh start
    WARNING: This will delete everything - documents, vectors, analytics, etc.
    """
    try:
        if not redis_client.client:
            raise HTTPException(status_code=500, detail="Redis client not available")
        
        vector_service = VectorSearchService()
        index_name = vector_service.vector_index_name
        
        deleted_counts = {
            "documents": 0,
            "vectors": 0,
            "chunks": 0,
            "analytics": 0,
            "other_keys": 0
        }
        
        # Step 1: Drop vector index
        try:
            redis_client.client.ft(index_name).dropindex(delete_documents=True)
            logger.info(f"Dropped vector index: {index_name}")
            index_dropped = True
        except Exception as e:
            logger.info(f"No vector index to drop: {e}")
            index_dropped = False
        
        # Step 2: Delete all document keys (doc:*)
        doc_keys = []
        for key in redis_client.client.scan_iter(match="doc:*"):
            doc_keys.append(key.decode() if isinstance(key, bytes) else key)
        if doc_keys:
            redis_client.client.delete(*doc_keys)
            deleted_counts["documents"] = len(doc_keys)
            logger.info(f"Deleted {len(doc_keys)} document keys")
        
        # Step 3: Delete all vector keys (vector:*)
        vector_keys = []
        for key in redis_client.client.scan_iter(match="vector:*"):
            vector_keys.append(key.decode() if isinstance(key, bytes) else key)
        if vector_keys:
            redis_client.client.delete(*vector_keys)
            deleted_counts["vectors"] = len(vector_keys)
            logger.info(f"Deleted {len(vector_keys)} vector keys")
        
        # Step 4: Delete all chunk keys (chunk:*)
        chunk_keys = []
        for key in redis_client.client.scan_iter(match="chunk:*"):
            chunk_keys.append(key.decode() if isinstance(key, bytes) else key)
        if chunk_keys:
            redis_client.client.delete(*chunk_keys)
            deleted_counts["chunks"] = len(chunk_keys)
            logger.info(f"Deleted {len(chunk_keys)} chunk keys")
        
        # Step 5: Delete analytics/stats keys
        stats_keys = []
        for pattern in ["stats:*", "analytics:*", "cache:*"]:
            for key in redis_client.client.scan_iter(match=pattern):
                stats_keys.append(key.decode() if isinstance(key, bytes) else key)
        if stats_keys:
            redis_client.client.delete(*stats_keys)
            deleted_counts["analytics"] = len(stats_keys)
            logger.info(f"Deleted {len(stats_keys)} analytics keys")
        
        # Step 6: Delete document index set
        try:
            redis_client.client.delete("doc:index")
            logger.info("Deleted document index set")
        except Exception as e:
            logger.info(f"No document index to delete: {e}")
        
        # Step 7: Recreate clean vector index
        await vector_service.initialize_vector_index()
        logger.info(f"Recreated clean vector index: {index_name}")
        
        # Step 8: Verify clean state
        try:
            index_info = redis_client.client.ft(index_name).info()
            new_index_created = True
            num_docs = index_info.get('num_docs', 0)
        except Exception:
            new_index_created = False
            num_docs = -1
        
        return {
            "success": True,
            "message": "All data cleared successfully - complete fresh start",
            "details": {
                "index_dropped": index_dropped,
                "new_index_created": new_index_created,
                "index_name": index_name,
                "deleted_counts": deleted_counts,
                "total_deleted": sum(deleted_counts.values()),
                "final_index_docs": num_docs
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to clear all data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

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
