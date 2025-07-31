from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.services.document_processor import document_processor
from app.database.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/rebuild-index")
async def rebuild_document_index():
    """Manually rebuild the document index from existing documents"""
    try:
        if not redis_client.client:
            raise HTTPException(status_code=500, detail="Redis client not available")
        
        # Clear existing index
        redis_client.client.delete("doc:index")
        logger.info("Cleared existing doc:index")
        
        # Scan for all doc: keys (excluding chunks and other metadata)
        all_keys = redis_client.client.keys("doc:*")
        doc_keys = [key for key in all_keys if not key.startswith((b"doc:chunk:", b"doc:chunks:", b"doc:indexed:"))]
        doc_ids = [key.decode().replace("doc:", "") if isinstance(key, bytes) else key.replace("doc:", "") for key in doc_keys]
        
        logger.info(f"Found {len(doc_ids)} documents to index")
        
        # Rebuild the index
        if doc_ids:
            redis_client.client.sadd("doc:index", *doc_ids)
            logger.info(f"Rebuilt doc:index with {len(doc_ids)} documents")
        
        # Verify the rebuild
        index_count = redis_client.client.scard("doc:index")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Document index rebuilt successfully",
                "documents_found": len(doc_ids),
                "index_count": index_count,
                "doc_ids": doc_ids[:10]  # Show first 10 for verification
            }
        )
        
    except Exception as e:
        logger.error(f"Index rebuild error: {e}")
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")

@router.get("/debug-redis")
async def debug_redis_keys():
    """Debug Redis keys to understand the data structure"""
    try:
        if not redis_client.client:
            raise HTTPException(status_code=500, detail="Redis client not available")
        
        # Get all keys
        all_keys = redis_client.client.keys("*")
        
        # Categorize keys
        doc_keys = [key for key in all_keys if key.startswith(b"doc:") and not key.startswith((b"doc:chunk:", b"doc:chunks:", b"doc:indexed:"))]
        chunk_keys = [key for key in all_keys if key.startswith(b"doc:chunk:")]
        chunks_keys = [key for key in all_keys if key.startswith(b"doc:chunks:")]
        index_keys = [key for key in all_keys if key == b"doc:index"]
        stats_keys = [key for key in all_keys if key.startswith(b"stats:")]
        
        # Get index content
        index_content = list(redis_client.client.smembers("doc:index")) if redis_client.client.exists("doc:index") else []
        
        return {
            "total_keys": len(all_keys),
            "doc_keys": len(doc_keys),
            "chunk_keys": len(chunk_keys),
            "chunks_keys": len(chunks_keys),
            "index_exists": len(index_keys) > 0,
            "index_count": len(index_content),
            "sample_doc_keys": [key.decode() for key in doc_keys[:5]],
            "sample_chunk_keys": [key.decode() for key in chunk_keys[:5]],
            "index_content_sample": [item.decode() if isinstance(item, bytes) else item for item in index_content[:5]],
            "stats_keys": [key.decode() for key in stats_keys]
        }
        
    except Exception as e:
        logger.error(f"Redis debug error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis debug failed: {str(e)}")
