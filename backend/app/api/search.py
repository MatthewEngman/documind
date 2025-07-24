"""
Search API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
import time
import hashlib

from app.database.models import SearchQuery, SearchResponse, SearchResult
from app.database.redis_client import redis_client
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])

# Initialize services
search_service = SearchService()
embedding_service = EmbeddingService()

@router.post("/", response_model=SearchResponse)
async def search_documents(query: SearchQuery):
    """
    Search documents using semantic similarity
    """
    start_time = time.time()
    
    try:
        # Generate query hash for caching
        query_hash = hashlib.md5(
            f"{query.query}_{query.limit}_{query.threshold}".encode()
        ).hexdigest()
        
        # Check cache first
        cached_results = redis_client.get_cached_search(query_hash)
        if cached_results:
            processing_time = time.time() - start_time
            
            # Increment cache hit counter
            redis_client.increment_counter("stats:cache_hits")
            
            return SearchResponse(
                query=query.query,
                results=[SearchResult(**result) for result in cached_results["results"]],
                total_results=len(cached_results["results"]),
                processing_time=processing_time,
                cached=True
            )
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query.query)
        
        # Perform vector search
        search_results = await search_service.search_similar_documents(
            query_embedding=query_embedding,
            limit=query.limit,
            threshold=query.threshold,
            filters=query.filters
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            search_result = SearchResult(
                document_id=result["document_id"],
                filename=result["filename"],
                similarity_score=result["similarity_score"],
                matched_chunk=result["matched_chunk"],
                chunk_index=result["chunk_index"],
                metadata=result.get("metadata") if query.include_metadata else None,
                highlight=result.get("highlight")
            )
            formatted_results.append(search_result)
        
        processing_time = time.time() - start_time
        
        # Cache results
        cache_data = [result.dict() for result in formatted_results]
        redis_client.cache_search_result(query_hash, cache_data)
        
        # Increment search counter
        redis_client.increment_counter("stats:total_searches")
        
        # Update response time stats
        redis_client.client.lpush("stats:response_times", processing_time)
        redis_client.client.ltrim("stats:response_times", 0, 999)  # Keep last 1000
        
        logger.info(f"Search completed: {len(formatted_results)} results in {processing_time:.3f}s")
        
        return SearchResponse(
            query=query.query,
            results=formatted_results,
            total_results=len(formatted_results),
            processing_time=processing_time,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=2)):
    """
    Get search suggestions based on query prefix
    """
    try:
        # Get popular queries from Redis
        popular_queries = redis_client.client.zrevrange("stats:popular_queries", 0, 9)
        
        # Filter suggestions based on query prefix
        suggestions = [
            query for query in popular_queries 
            if query.lower().startswith(q.lower())
        ]
        
        return {"suggestions": suggestions[:5]}
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

@router.get("/history")
async def get_search_history(limit: int = Query(default=10, le=50)):
    """
    Get recent search history
    """
    try:
        # Get recent searches from Redis
        recent_searches = redis_client.client.lrange("stats:recent_searches", 0, limit - 1)
        
        return {"recent_searches": recent_searches}
        
    except Exception as e:
        logger.error(f"Failed to get search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search history")

@router.delete("/cache")
async def clear_search_cache():
    """
    Clear search result cache
    """
    try:
        # Get all cache keys
        cache_keys = redis_client.client.keys("cache:search:*")
        
        if cache_keys:
            redis_client.client.delete(*cache_keys)
            logger.info(f"Cleared {len(cache_keys)} cached search results")
        
        return {"message": f"Cleared {len(cache_keys)} cached results"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")
