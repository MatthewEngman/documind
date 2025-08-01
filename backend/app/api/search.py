from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import time
import hashlib
import json
from datetime import datetime

from app.database.redis_client import redis_client
from app.services.vector_search_service import vector_search_service
from app.services.embedding_service import embedding_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])

# Pydantic models for API
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None
    include_content: bool = Field(default=True)
    include_metadata: bool = Field(default=True)

class SearchResult(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    title: str
    filename: str
    similarity_score: float
    word_count: int
    chunk_index: int
    tags: List[str]
    upload_date: str
    embedding_method: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float
    cached: bool
    search_id: str

@router.post("/", response_model=SearchResponse)
async def search_documents(query: SearchQuery, background_tasks: BackgroundTasks):
    """
    Perform semantic search across document chunks
    """
    start_time = time.time()
    search_id = hashlib.md5(f"{query.query}_{time.time()}".encode()).hexdigest()[:12]
    
    try:
        # Generate cache key
        cache_key = f"search_cache:{hashlib.md5(json.dumps(query.dict(), sort_keys=True).encode()).hexdigest()}"
        
        # Check cache first if enabled
        if settings.enable_search_cache:
            cached_result = redis_client.client.get(cache_key)
            if cached_result:
                cached_data = json.loads(cached_result)
                processing_time = time.time() - start_time
                
                # Update analytics
                redis_client.client.incr("stats:cache_hits")
                
                logger.info(f"Cache hit for search: {query.query[:50]}...")
                
                return SearchResponse(
                    query=query.query,
                    results=[SearchResult(**result) for result in cached_data["results"]],
                    total_results=len(cached_data["results"]),
                    processing_time=processing_time,
                    cached=True,
                    search_id=search_id
                )
        
        # Perform vector search
        search_results = await vector_search_service.search_vectors(
            query=query.query,
            limit=query.limit,
            filters=query.filters,
            similarity_threshold=query.similarity_threshold
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            search_result = SearchResult(
                chunk_id=result["chunk_id"],
                doc_id=result["doc_id"],
                content=result["content"] if query.include_content else "",
                title=result["title"],
                filename=result["filename"],
                similarity_score=result["similarity_score"],
                word_count=result["word_count"],
                chunk_index=result["chunk_index"],
                tags=result["tags"],
                upload_date=result["upload_date"],
                embedding_method=result["embedding_method"]
            )
            formatted_results.append(search_result)
        
        processing_time = time.time() - start_time
        
        # Cache results if enabled
        if settings.enable_search_cache and formatted_results:
            cache_data = {
                "results": [result.dict() for result in formatted_results],
                "timestamp": datetime.utcnow().isoformat()
            }
            redis_client.client.setex(
                cache_key, 
                settings.search_cache_ttl, 
                json.dumps(cache_data)
            )
        
        # Update analytics immediately (more reliable than background tasks)
        logger.info(f"📊 Updating analytics immediately for search {search_id}")
        try:
            # Increment total searches immediately
            new_total = redis_client.client.incr("stats:total_searches")
            logger.info(f"📊 Total searches incremented to: {new_total}")
            
            # Add to popular queries
            redis_client.client.zincrby("stats:popular_queries", 1, query.query)
            
            # Add response time
            redis_client.client.lpush("stats:response_times", processing_time)
            redis_client.client.ltrim("stats:response_times", 0, 999)
            
            logger.info(f"✅ Analytics updated immediately for search {search_id}")
        except Exception as analytics_error:
            logger.error(f"❌ Immediate analytics update failed: {analytics_error}")
        
        # Also add background task as backup
        logger.info(f"🔄 Adding background task as backup for search {search_id}")
        background_tasks.add_task(
            _update_search_analytics,
            query.query,
            len(formatted_results),
            processing_time,
            search_id
        )
        
        logger.info(f"Search completed: {len(formatted_results)} results in {processing_time:.3f}s")
        
        return SearchResponse(
            query=query.query,
            results=formatted_results,
            total_results=len(formatted_results),
            processing_time=processing_time,
            cached=False,
            search_id=search_id
        )
        
    except Exception as e:
        logger.error(f"Search failed for query '{query.query}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=2, max_length=100)):
    """
    Get search suggestions based on query prefix and popular searches
    """
    try:
        suggestions = []
        
        # Get popular queries from Redis
        popular_queries = redis_client.client.zrevrange("stats:popular_queries", 0, 19, withscores=True)
        
        # Filter suggestions based on query prefix
        for query_data in popular_queries:
            if isinstance(query_data, tuple):
                query, score = query_data
                query = query.decode() if isinstance(query, bytes) else query
            else:
                query = query_data.decode() if isinstance(query_data, bytes) else query_data
                score = 1
            
            if query.lower().startswith(q.lower()):
                suggestions.append({
                    "query": query,
                    "score": int(score) if isinstance(score, (int, float)) else 1
                })
        
        # Sort by score and limit
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "suggestions": [s["query"] for s in suggestions[:8]],
            "query_prefix": q
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestions for '{q}': {e}")
        return {"suggestions": [], "query_prefix": q}

@router.get("/analytics")
async def get_search_analytics():
    """
    Get search analytics and statistics
    """
    try:
        # Initialize default values
        total_searches = 0
        cache_hits = 0
        avg_response_time = 0
        popular_list = []
        vector_stats = {"status": "error", "error": "Service unavailable"}
        embedding_stats = {"cache_size": 0, "openai_available": False, "local_model_available": False, "default_method": "none"}
        
        # Get various analytics from Redis with error handling
        try:
            if redis_client.client:
                total_searches = int(redis_client.client.get("stats:total_searches") or 0)
                cache_hits = int(redis_client.client.get("stats:cache_hits") or 0)
                
                # Get recent response times
                response_times = redis_client.client.lrange("stats:response_times", 0, 99)
                if response_times:
                    times = [float(t) for t in response_times if t]
                    avg_response_time = sum(times) / len(times) if times else 0
                
                # Get popular queries
                popular_queries = redis_client.client.zrevrange("stats:popular_queries", 0, 9, withscores=True)
                for query_data in popular_queries:
                    if isinstance(query_data, tuple):
                        query, count = query_data
                        query = query.decode() if isinstance(query, bytes) else query
                        popular_list.append({"query": query, "count": int(count)})
        except Exception as redis_error:
            logger.warning(f"Redis analytics error: {redis_error}")
        
        # Get vector search stats with error handling
        try:
            vector_stats = vector_search_service.get_vector_stats()
        except Exception as vector_error:
            logger.warning(f"Vector stats error: {vector_error}")
            vector_stats = {"status": "error", "error": str(vector_error)}
        
        # Get embedding stats with error handling
        try:
            embedding_stats = embedding_service.get_embedding_stats()
        except Exception as embedding_error:
            logger.warning(f"Embedding stats error: {embedding_error}")
            embedding_stats = {"cache_size": 0, "openai_available": False, "local_model_available": False, "default_method": "error"}
        
        return {
            "search_stats": {
                "total_searches": total_searches,
                "cache_hits": cache_hits,
                "cache_hit_rate": round(cache_hits / max(total_searches, 1) * 100, 2),
                "avg_response_time": round(avg_response_time, 3)
            },
            "popular_queries": popular_list,
            "vector_stats": vector_stats,
            "embedding_stats": embedding_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        # Return fallback data instead of raising exception
        return {
            "search_stats": {
                "total_searches": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0,
                "avg_response_time": 0
            },
            "popular_queries": [],
            "vector_stats": {"status": "error", "error": "Service unavailable"},
            "embedding_stats": {"cache_size": 0, "openai_available": False, "local_model_available": False, "default_method": "error"}
        }

@router.delete("/cache")
async def clear_search_cache():
    """
    Clear search result cache
    """
    try:
        # Get all search cache keys
        cache_keys = redis_client.client.keys("search_cache:*")
        
        cleared_count = 0
        if cache_keys:
            redis_client.client.delete(*cache_keys)
            cleared_count = len(cache_keys)
            logger.info(f"Cleared {cleared_count} cached search results")
        
        return {
            "message": f"Cleared {cleared_count} cached search results",
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear search cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

# Background task for updating search analytics
async def _update_search_analytics(query: str, result_count: int, processing_time: float, search_id: str):
    """
    Update search analytics in the background
    """
    try:
        logger.info(f"📊 Updating analytics for search {search_id}: query='{query[:30]}...', results={result_count}")
        
        # Increment total searches
        new_total = redis_client.client.incr("stats:total_searches")
        logger.info(f"📊 Total searches incremented to: {new_total}")
        
        # Add to popular queries (with score increment)
        redis_client.client.zincrby("stats:popular_queries", 1, query)
        
        # Add to recent searches
        redis_client.client.lpush("stats:recent_searches", query)
        redis_client.client.ltrim("stats:recent_searches", 0, 99)  # Keep last 100
        
        # Add response time
        redis_client.client.lpush("stats:response_times", processing_time)
        redis_client.client.ltrim("stats:response_times", 0, 999)  # Keep last 1000
        
        # Log search event
        search_log = {
            "search_id": search_id,
            "query": query,
            "result_count": result_count,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        redis_client.client.lpush("logs:searches", json.dumps(search_log))
        redis_client.client.ltrim("logs:searches", 0, 999)  # Keep last 1000 searches
        
        logger.info(f"✅ Analytics updated successfully for search {search_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to update search analytics: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
