"""
Cache utilities for DocuMind application
"""
import logging
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import pickle
import base64

from app.database.redis_client import redis_client
from app.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced cache management utilities"""
    
    def __init__(self):
        self.default_ttl = settings.cache_ttl
        self.key_prefix = "cache:"
    
    def _generate_cache_key(self, namespace: str, key: str, params: Optional[Dict] = None) -> str:
        """
        Generate a consistent cache key
        """
        try:
            # Include parameters in key if provided
            if params:
                param_str = json.dumps(params, sort_keys=True)
                key_data = f"{namespace}:{key}:{param_str}"
            else:
                key_data = f"{namespace}:{key}"
            
            # Hash long keys to avoid Redis key length limits
            if len(key_data) > 200:
                key_hash = hashlib.md5(key_data.encode()).hexdigest()
                return f"{self.key_prefix}{namespace}:{key_hash}"
            
            return f"{self.key_prefix}{namespace}:{key}"
            
        except Exception as e:
            logger.error(f"Cache key generation failed: {e}")
            return f"{self.key_prefix}{namespace}:{key}"
    
    def set(
        self, 
        namespace: str, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        params: Optional[Dict] = None
    ) -> bool:
        """
        Set a value in cache
        """
        try:
            cache_key = self._generate_cache_key(namespace, key, params)
            ttl = ttl or self.default_ttl
            
            # Serialize value
            serialized_value = self._serialize_value(value)
            
            # Store in Redis with metadata
            cache_data = {
                "value": serialized_value,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": ttl,
                "namespace": namespace,
                "original_key": key
            }
            
            redis_client.set_json(cache_key, cache_data, ttl)
            logger.debug(f"Cached: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for {namespace}:{key}: {e}")
            return False
    
    def get(
        self, 
        namespace: str, 
        key: str, 
        params: Optional[Dict] = None,
        default: Any = None
    ) -> Any:
        """
        Get a value from cache
        """
        try:
            cache_key = self._generate_cache_key(namespace, key, params)
            
            cache_data = redis_client.get_json(cache_key)
            if not cache_data:
                logger.debug(f"Cache miss: {cache_key}")
                return default
            
            # Deserialize value
            value = self._deserialize_value(cache_data.get("value"))
            logger.debug(f"Cache hit: {cache_key}")
            return value
            
        except Exception as e:
            logger.error(f"Cache get failed for {namespace}:{key}: {e}")
            return default
    
    def delete(self, namespace: str, key: str, params: Optional[Dict] = None) -> bool:
        """
        Delete a value from cache
        """
        try:
            cache_key = self._generate_cache_key(namespace, key, params)
            result = redis_client.client.delete(cache_key)
            
            if result:
                logger.debug(f"Cache deleted: {cache_key}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete failed for {namespace}:{key}: {e}")
            return False
    
    def exists(self, namespace: str, key: str, params: Optional[Dict] = None) -> bool:
        """
        Check if a key exists in cache
        """
        try:
            cache_key = self._generate_cache_key(namespace, key, params)
            return bool(redis_client.client.exists(cache_key))
            
        except Exception as e:
            logger.error(f"Cache exists check failed for {namespace}:{key}: {e}")
            return False
    
    def clear_namespace(self, namespace: str) -> int:
        """
        Clear all keys in a namespace
        """
        try:
            pattern = f"{self.key_prefix}{namespace}:*"
            keys = redis_client.client.keys(pattern)
            
            if keys:
                deleted = redis_client.client.delete(*keys)
                logger.info(f"Cleared {deleted} keys from namespace: {namespace}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache namespace clear failed for {namespace}: {e}")
            return 0
    
    def get_cache_info(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cache statistics and information
        """
        try:
            if namespace:
                pattern = f"{self.key_prefix}{namespace}:*"
            else:
                pattern = f"{self.key_prefix}*"
            
            keys = redis_client.client.keys(pattern)
            
            # Analyze cache data
            total_keys = len(keys)
            total_size = 0
            namespaces = {}
            oldest_entry = None
            newest_entry = None
            
            for key in keys:
                try:
                    cache_data = redis_client.get_json(key)
                    if cache_data:
                        # Track namespace statistics
                        ns = cache_data.get("namespace", "unknown")
                        if ns not in namespaces:
                            namespaces[ns] = {"count": 0, "size_estimate": 0}
                        
                        namespaces[ns]["count"] += 1
                        
                        # Estimate size (rough)
                        size_estimate = len(json.dumps(cache_data))
                        total_size += size_estimate
                        namespaces[ns]["size_estimate"] += size_estimate
                        
                        # Track timestamps
                        cached_at = cache_data.get("cached_at")
                        if cached_at:
                            if not oldest_entry or cached_at < oldest_entry:
                                oldest_entry = cached_at
                            if not newest_entry or cached_at > newest_entry:
                                newest_entry = cached_at
                                
                except Exception as e:
                    logger.warning(f"Failed to analyze cache key {key}: {e}")
                    continue
            
            return {
                "total_keys": total_keys,
                "total_size_estimate": f"{total_size / 1024:.2f} KB",
                "namespaces": namespaces,
                "oldest_entry": oldest_entry,
                "newest_entry": newest_entry,
                "default_ttl": self.default_ttl,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cache info retrieval failed: {e}")
            return {"error": "Failed to get cache info"}
    
    def _serialize_value(self, value: Any) -> str:
        """
        Serialize value for storage
        """
        try:
            # Handle different data types
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                return json.dumps(value)
            else:
                # Use pickle for complex objects
                pickled = pickle.dumps(value)
                encoded = base64.b64encode(pickled).decode('utf-8')
                return f"pickle:{encoded}"
                
        except Exception as e:
            logger.error(f"Value serialization failed: {e}")
            return json.dumps(str(value))
    
    def _deserialize_value(self, serialized: str) -> Any:
        """
        Deserialize value from storage
        """
        try:
            if serialized.startswith("pickle:"):
                # Handle pickled objects
                encoded = serialized[7:]  # Remove "pickle:" prefix
                pickled = base64.b64decode(encoded.encode('utf-8'))
                return pickle.loads(pickled)
            else:
                # Handle JSON
                return json.loads(serialized)
                
        except Exception as e:
            logger.error(f"Value deserialization failed: {e}")
            return serialized
    
    def cache_decorator(self, namespace: str, ttl: Optional[int] = None, key_func: Optional[callable] = None):
        """
        Decorator for caching function results
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    # Generate cache key
                    if key_func:
                        cache_key = key_func(*args, **kwargs)
                    else:
                        # Default key generation
                        key_parts = [func.__name__]
                        if args:
                            key_parts.extend([str(arg) for arg in args])
                        if kwargs:
                            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                        cache_key = "_".join(key_parts)
                    
                    # Try to get from cache
                    cached_result = self.get(namespace, cache_key)
                    if cached_result is not None:
                        return cached_result
                    
                    # Execute function and cache result
                    result = func(*args, **kwargs)
                    self.set(namespace, cache_key, result, ttl)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Cache decorator failed for {func.__name__}: {e}")
                    # Execute function without caching
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator

class SearchCache:
    """Specialized cache for search operations"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.namespace = "search"
    
    def cache_search_result(self, query: str, results: List[Dict], filters: Optional[Dict] = None) -> bool:
        """
        Cache search results
        """
        try:
            # Generate cache key based on query and filters
            key_data = {"query": query}
            if filters:
                key_data["filters"] = filters
            
            cache_key = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
            
            cache_data = {
                "query": query,
                "filters": filters,
                "results": results,
                "result_count": len(results),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            return self.cache_manager.set(self.namespace, cache_key, cache_data)
            
        except Exception as e:
            logger.error(f"Search result caching failed: {e}")
            return False
    
    def get_cached_search(self, query: str, filters: Optional[Dict] = None) -> Optional[List[Dict]]:
        """
        Get cached search results
        """
        try:
            key_data = {"query": query}
            if filters:
                key_data["filters"] = filters
            
            cache_key = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
            
            cached_data = self.cache_manager.get(self.namespace, cache_key)
            if cached_data and isinstance(cached_data, dict):
                return cached_data.get("results", [])
            
            return None
            
        except Exception as e:
            logger.error(f"Search cache retrieval failed: {e}")
            return None
    
    def invalidate_document_cache(self, document_id: str) -> int:
        """
        Invalidate cache entries that might contain results from a specific document
        """
        try:
            # This is a simplified approach - in production, you might want to
            # maintain a reverse index of document_id -> cache_keys
            
            # For now, we'll clear the entire search cache when a document changes
            return self.cache_manager.clear_namespace(self.namespace)
            
        except Exception as e:
            logger.error(f"Document cache invalidation failed for {document_id}: {e}")
            return 0

class EmbeddingCache:
    """Specialized cache for embeddings"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.namespace = "embeddings"
    
    def cache_embedding(self, text: str, embedding: List[float], model: str) -> bool:
        """
        Cache text embedding
        """
        try:
            # Use text hash as key to handle long texts
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            cache_key = f"{model}_{text_hash}"
            
            cache_data = {
                "text_hash": text_hash,
                "embedding": embedding,
                "model": model,
                "dimension": len(embedding),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Cache embeddings for longer (they're expensive to compute)
            return self.cache_manager.set(self.namespace, cache_key, cache_data, ttl=86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Embedding caching failed: {e}")
            return False
    
    def get_cached_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """
        Get cached embedding
        """
        try:
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            cache_key = f"{model}_{text_hash}"
            
            cached_data = self.cache_manager.get(self.namespace, cache_key)
            if cached_data and isinstance(cached_data, dict):
                return cached_data.get("embedding")
            
            return None
            
        except Exception as e:
            logger.error(f"Embedding cache retrieval failed: {e}")
            return None

# Global cache instances
cache_manager = CacheManager()
search_cache = SearchCache()
embedding_cache = EmbeddingCache()
