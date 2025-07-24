"""
Analytics API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging
from datetime import datetime, timedelta

from app.database.models import AnalyticsData
from app.database.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/", response_model=AnalyticsData)
async def get_analytics():
    """
    Get comprehensive analytics data
    """
    try:
        # Get basic counters
        total_documents = redis_client.client.get("stats:total_documents") or 0
        total_searches = redis_client.client.get("stats:total_searches") or 0
        cache_hits = redis_client.client.get("stats:cache_hits") or 0
        
        # Convert to integers
        total_documents = int(total_documents)
        total_searches = int(total_searches)
        cache_hits = int(cache_hits)
        
        # Calculate cache hit rate
        cache_hit_rate = (cache_hits / total_searches * 100) if total_searches > 0 else 0
        
        # Get average response time
        response_times = redis_client.client.lrange("stats:response_times", 0, -1)
        avg_response_time = 0
        if response_times:
            times = [float(t) for t in response_times]
            avg_response_time = sum(times) / len(times)
        
        # Get popular queries
        popular_queries_raw = redis_client.client.zrevrange("stats:popular_queries", 0, 9, withscores=True)
        popular_queries = [query.decode() if isinstance(query, bytes) else query for query, _ in popular_queries_raw]
        
        # Get document type distribution
        doc_keys = redis_client.client.keys("doc:meta:*")
        document_types = {"pdf": 0, "docx": 0, "txt": 0}
        
        for key in doc_keys:
            metadata = redis_client.get_json(key)
            if metadata and "file_type" in metadata:
                file_type = metadata["file_type"]
                if file_type in document_types:
                    document_types[file_type] += 1
        
        # Get Redis memory usage
        redis_info = redis_client.client.info("memory")
        storage_used = redis_info.get("used_memory_human", "0B")
        
        return AnalyticsData(
            total_documents=total_documents,
            total_searches=total_searches,
            avg_response_time=round(avg_response_time, 3),
            cache_hit_rate=round(cache_hit_rate, 2),
            storage_used=storage_used,
            popular_queries=popular_queries,
            document_types=document_types
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@router.get("/performance")
async def get_performance_metrics():
    """
    Get detailed performance metrics
    """
    try:
        # Get response time statistics
        response_times = redis_client.client.lrange("stats:response_times", 0, -1)
        times = [float(t) for t in response_times] if response_times else []
        
        performance_data = {
            "response_times": {
                "count": len(times),
                "average": round(sum(times) / len(times), 3) if times else 0,
                "min": round(min(times), 3) if times else 0,
                "max": round(max(times), 3) if times else 0,
                "median": round(sorted(times)[len(times)//2], 3) if times else 0
            },
            "redis_stats": redis_client.get_stats(),
            "cache_performance": {
                "total_searches": int(redis_client.client.get("stats:total_searches") or 0),
                "cache_hits": int(redis_client.client.get("stats:cache_hits") or 0),
                "cache_misses": int(redis_client.client.get("stats:total_searches") or 0) - int(redis_client.client.get("stats:cache_hits") or 0)
            }
        }
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.get("/usage")
async def get_usage_statistics():
    """
    Get usage statistics over time
    """
    try:
        # Get hourly usage data (last 24 hours)
        now = datetime.utcnow()
        hourly_data = []
        
        for i in range(24):
            hour = now - timedelta(hours=i)
            hour_key = f"stats:hourly:{hour.strftime('%Y%m%d%H')}"
            
            searches = redis_client.client.hget(hour_key, "searches") or 0
            uploads = redis_client.client.hget(hour_key, "uploads") or 0
            
            hourly_data.append({
                "hour": hour.strftime('%Y-%m-%d %H:00'),
                "searches": int(searches),
                "uploads": int(uploads)
            })
        
        # Reverse to show oldest first
        hourly_data.reverse()
        
        return {
            "hourly_usage": hourly_data,
            "summary": {
                "total_searches_24h": sum(h["searches"] for h in hourly_data),
                "total_uploads_24h": sum(h["uploads"] for h in hourly_data),
                "peak_hour": max(hourly_data, key=lambda x: x["searches"])["hour"] if hourly_data else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage statistics")

@router.post("/reset")
async def reset_analytics():
    """
    Reset analytics counters (admin function)
    """
    try:
        # Reset counters
        counters_to_reset = [
            "stats:total_documents",
            "stats:total_searches", 
            "stats:cache_hits"
        ]
        
        for counter in counters_to_reset:
            redis_client.client.set(counter, 0)
        
        # Clear lists
        lists_to_clear = [
            "stats:response_times",
            "stats:recent_searches"
        ]
        
        for list_key in lists_to_clear:
            redis_client.client.delete(list_key)
        
        # Clear sorted sets
        redis_client.client.delete("stats:popular_queries")
        
        # Clear hourly stats
        hourly_keys = redis_client.client.keys("stats:hourly:*")
        if hourly_keys:
            redis_client.client.delete(*hourly_keys)
        
        logger.info("Analytics data reset successfully")
        
        return {"message": "Analytics data reset successfully"}
        
    except Exception as e:
        logger.error(f"Failed to reset analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset analytics")
