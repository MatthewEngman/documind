from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.database.redis_client import redis_client
from app.api import documents, search, admin, vector_admin
from app.services.vector_search_service import vector_search_service
from app.services.embedding_service import embedding_service

# DocuMind Backend API
# FastAPI application for document processing and semantic search
# Updated: Search functionality fix with OpenAI API key, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version: Bug fixes for duplicate uploads and UI improvements - triggering deployment

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting DocuMind API...")
    
    redis_required = os.getenv("REDIS_REQUIRED", "true").lower() == "true"
    
    # Verify Redis connection
    redis_healthy = False
    try:
        redis_healthy = redis_client.health_check()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
    
    if redis_required and not redis_healthy:
        raise Exception("Redis connection failed during startup")
    elif not redis_healthy:
        logger.warning("⚠️ Redis connection failed - running in degraded mode")
    else:
        logger.info("✅ Redis connection established")
    
    # Initialize vector search service (only if Redis is available)
    if redis_healthy:
        try:
            await vector_search_service.initialize_vector_index()
            logger.info("📊 Vector search service initialized")
        except Exception as e:
            logger.warning(f"Vector index initialization failed: {e}")
    else:
        logger.info("📊 Skipping vector search initialization (Redis unavailable)")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DocuMind API...")

# Create FastAPI app
app = FastAPI(
    title="DocuMind API",
    description="Semantic Document Cache powered by Redis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Production-ready configuration
allowed_origins = [
    "https://documind-ruby.vercel.app",  # Production frontend
    "http://localhost:3000",  # Local development
    "http://localhost:3001",  # Local development (alternative port)
    "http://127.0.0.1:3000",  # Local development
    "http://127.0.0.1:3001",  # Local development (alternative port)
]

# Add environment-specific origins
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

# For production, allow all Vercel domains if needed
if os.getenv("ENVIRONMENT") == "production":
    allowed_origins.extend([
        "https://*.vercel.app",
        "https://vercel.app",
    ])

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("CORS_ALLOW_ALL") == "true" else allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
)

# CORS preflight handler
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "OK"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = redis_client.health_check()
    
    from datetime import datetime
    
    return {
        "status": "healthy" if redis_healthy else "unhealthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "version": "1.0.5",
        "timestamp": datetime.utcnow().isoformat()
    }

# Redis stats endpoint
@app.get("/api/stats")
async def get_redis_stats():
    """Get Redis usage statistics"""
    try:
        stats = redis_client.get_stats()
        return {
            "redis_stats": stats,
            "settings": {
                "max_file_size": settings.max_file_size,
                "cache_ttl": settings.cache_ttl,
                "embedding_model": settings.embedding_model
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include routers
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(vector_admin.router)

@app.post("/api/load-demo")
async def load_demo_data():
    """Load demo documents for showcase"""
    try:
        import sys
        import os
        import uuid
        from datetime import datetime
        
        SAMPLE_DOCS = [
            {
                "filename": "machine_learning_intro.txt",
                "content": "Machine Learning Introduction\n\nMachine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed..."
            },
            {
                "filename": "python_programming_guide.txt", 
                "content": "Python Programming Guide\n\nPython is a high-level, interpreted programming language with dynamic semantics..."
            },
            {
                "filename": "database_design_principles.txt",
                "content": "Database Design Principles\n\nDatabase design is the process of producing a detailed data model of a database..."
            },
            {
                "filename": "artificial_intelligence_overview.txt",
                "content": "Artificial Intelligence Overview\n\nArtificial Intelligence (AI) refers to the simulation of human intelligence in machines..."
            },
            {
                "filename": "data_science_methodology.txt",
                "content": "Data Science Methodology\n\nData science is an interdisciplinary field that uses scientific methods, processes, algorithms..."
            }
        ]
        
        loaded_count = 0
        
        for doc_data in SAMPLE_DOCS:
            doc_id = str(uuid.uuid4())
            
            doc_format = {
                "id": doc_id,
                "filename": doc_data["filename"],
                "title": doc_data["filename"].replace('.txt', '').replace('_', ' ').title(),
                "file_type": "txt",
                "file_size": len(doc_data["content"].encode('utf-8')),
                "word_count": len(doc_data["content"].split()),
                "language": "en",
                "created_at": datetime.utcnow().isoformat(),
                "processing_status": "completed"
            }
            
            redis_client.set_json(f"doc:{doc_id}", doc_format)
            redis_client.set_json(f"doc:content:{doc_id}", {
                "document_id": doc_id,
                "raw_text": doc_data["content"],
                "processed_timestamp": datetime.utcnow().isoformat()
            })
            
            try:
                redis_client.client.sadd("doc:index", doc_id)
            except AttributeError:
                if not hasattr(redis_client.client, '_sets'):
                    redis_client.client._sets = {}
                if "doc:index" not in redis_client.client._sets:
                    redis_client.client._sets["doc:index"] = set()
                redis_client.client._sets["doc:index"].add(doc_id)
            
            redis_client.increment_counter("stats:total_documents")
            loaded_count += 1
        
        return {"message": f"Successfully loaded {loaded_count} demo documents", "count": loaded_count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {str(e)}")

# System statistics endpoint
@app.get("/api/system/stats")
async def get_system_stats():
    """Get comprehensive system statistics including search analytics"""
    try:
        redis_stats = redis_client.get_stats()
        
        # Get document statistics
        if redis_client.client:
            total_docs_counter = redis_client.client.get("stats:total_documents")
            if total_docs_counter:
                total_docs = int(total_docs_counter)
            else:
                total_docs = redis_client.client.scard("doc:index") if hasattr(redis_client.client, 'scard') else 0
            
            processed_docs = redis_client.client.get("stats:documents_processed") or 0
            chunks_created = redis_client.client.get("stats:chunks_created") or 0
            
            # Get search analytics
            total_searches = int(redis_client.client.get("stats:total_searches") or 0)
            cache_hits = int(redis_client.client.get("stats:cache_hits") or 0)
        else:
            total_docs = processed_docs = chunks_created = 0
            total_searches = cache_hits = 0
        
        # Get embedding service status
        try:
            embedding_stats = embedding_service.get_embedding_stats()
            openai_available = embedding_stats.get("openai_available", False)
            local_model_available = embedding_stats.get("local_model_available", False)
        except Exception as e:
            logger.warning(f"Embedding stats error: {e}")
            openai_available = False
            local_model_available = False
        
        # Calculate cache hit rate
        cache_hit_rate = round(cache_hits / max(total_searches, 1) * 100, 2) if total_searches > 0 else 0
        
        return {
            "system": {
                "status": "healthy",
                "redis_connected": redis_client.health_check()
            },
            "redis": redis_stats,
            "documents": {
                "total_documents": int(total_docs),
                "processed_documents": int(processed_docs),
                "total_chunks": int(chunks_created)
            },
            "search": {
                "total_searches": total_searches,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hit_rate
            },
            "services": {
                "openai_available": openai_available,
                "local_model_available": local_model_available,
                "redis_connected": redis_client.health_check()
            }
        }
        
    except Exception as e:
        logger.error(f"System stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for development"""
    return {
        "message": "DocuMind API is running!",
        "redis_connected": redis_client.health_check()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
