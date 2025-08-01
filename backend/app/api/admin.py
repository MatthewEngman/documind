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
async def debug_redis():
    """Debug Redis keys and data"""
    try:
        # Get all Redis keys
        all_keys = redis_client.client.keys("*")
        
        # Categorize keys
        doc_keys = [key for key in all_keys if key.startswith(b"doc:") and not key.startswith((b"doc:chunk:", b"doc:chunks:", b"doc:indexed:"))]
        chunk_keys = [key for key in all_keys if key.startswith(b"doc:chunk:")]
        index_keys = [key for key in all_keys if key.startswith(b"doc:chunks:")]
        
        # Get doc:index set
        doc_index = list(redis_client.client.smembers("doc:index"))
        
        return {
            "total_keys": len(all_keys),
            "document_keys": len(doc_keys),
            "chunk_keys": len(chunk_keys),
            "index_keys": len(index_keys),
            "doc_index_size": len(doc_index),
            "sample_doc_keys": [key.decode() for key in doc_keys[:5]],
            "doc_index_sample": [doc_id.decode() if isinstance(doc_id, bytes) else doc_id for doc_id in doc_index[:5]]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis debug failed: {str(e)}")

@router.get("/debug-env")
async def debug_environment():
    """Debug environment variables and OpenAI configuration - SECURE VERSION"""
    import os
    from app.config import settings
    
    try:
        # Check environment variables (SECURE - no sensitive data exposed)
        env_openai_key = os.getenv('OPENAI_API_KEY')
        env_redis_required = os.getenv('REDIS_REQUIRED')
        
        # Check settings (SECURE - no sensitive data exposed)
        settings_openai_key = settings.openai_api_key
        
        return {
            "environment_variables": {
                "OPENAI_API_KEY": "present" if env_openai_key else "missing",
                "REDIS_REQUIRED": env_redis_required
            },
            "settings": {
                "openai_api_key": "present" if settings_openai_key else "missing",
                "embedding_model": settings.embedding_model,
                "redis_required": settings.redis_required
            },
            "configuration_status": {
                "openai_configured": bool(settings_openai_key),
                "redis_required": settings.redis_required,
                "keys_match": env_openai_key == settings_openai_key if env_openai_key and settings_openai_key else False
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Environment debug failed: {str(e)}")

@router.post("/test-openai")
async def test_openai_initialization():
    """Test OpenAI client initialization manually"""
    import openai
    import os
    from app.config import settings
    
    try:
        # Get the API key
        api_key = settings.openai_api_key
        if not api_key:
            return {
                "status": "failed",
                "error": "No OpenAI API key found in settings",
                "env_key_present": bool(os.getenv('OPENAI_API_KEY'))
            }
        
        # Try to create OpenAI client
        try:
            client = openai.OpenAI(api_key=api_key)
            
            # Test the client
            try:
                models_response = client.models.list()
                model_count = len(models_response.data)
                
                return {
                    "status": "success",
                    "client_created": True,
                    "models_available": model_count,
                    "api_key_length": len(api_key),
                    "api_key_prefix": api_key[:10]
                }
                    
            except Exception as api_error:
                return {
                    "status": "client_created_api_failed",
                    "client_created": True,
                    "api_test": "failed",
                    "api_error": str(api_error),
                    "api_key_length": len(api_key)
                }
                
        except Exception as client_error:
            return {
                "status": "client_creation_failed",
                "client_created": False,
                "client_error": str(client_error),
                "error_type": type(client_error).__name__,
                "api_key_length": len(api_key)
            }
            
    except Exception as e:
        return {
            "status": "unexpected_error",
            "error": str(e),
            "error_type": type(e).__name__
        }
