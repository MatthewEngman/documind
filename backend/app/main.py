from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.redis_client import redis_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting DocuMind API...")
    
    # Verify Redis connection
    if not redis_client.health_check():
        raise Exception("Redis connection failed during startup")
    
    # Initialize vector index (placeholder)
    try:
        # We'll implement this in the next phase
        logger.info("📊 Vector index initialization skipped for now")
    except Exception as e:
        logger.warning(f"Vector index initialization failed: {e}")
    
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = redis_client.health_check()
    
    return {
        "status": "healthy" if redis_healthy else "unhealthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "version": "1.0.0"
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
