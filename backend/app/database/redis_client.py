import redis
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client = None
        self.connect()
    
    def connect(self):
        """Establish Redis connection with retry logic"""
        try:
            # Use Redis URL matching the working CLI command format
            redis_url = f"redis://default:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}"
            
            self.client = redis.from_url(
                redis_url,
                decode_responses=settings.redis_decode_responses,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.client.ping()
            logger.info("✅ Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            return self.client.ping()
        except:
            return False
    
    # Vector Operations (Redis Stack)
    def create_vector_index(self, index_name: str, schema: Dict):
        """Create vector search index"""
        try:
            from redis.commands.search.field import VectorField, TextField, NumericField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            # Check if index exists
            try:
                self.client.ft(index_name).info()
                logger.info(f"Vector index '{index_name}' already exists")
                return
            except:
                pass
            
            # Create index
            self.client.ft(index_name).create_index(
                schema,
                definition=IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)
            )
            logger.info(f"✅ Vector index '{index_name}' created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create vector index: {e}")
            raise
    
    def add_document_vector(self, doc_id: str, vector: List[float], metadata: Dict):
        """Add document vector with metadata"""
        try:
            # Store as hash for vector search
            key = f"doc:{doc_id}"
            
            # Prepare data
            data = {
                "vector": self._serialize_vector(vector),
                **metadata
            }
            
            # Store in Redis
            self.client.hset(key, mapping=data)
            logger.debug(f"Stored vector for document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to store document vector: {e}")
            raise
    
    def search_vectors(self, query_vector: List[float], limit: int = 10, filters: Dict = None):
        """Search for similar vectors"""
        try:
            # This is a simplified version - you'll enhance this with actual vector search
            # For now, we'll implement basic functionality
            
            query = "*"
            if filters:
                # Add filters to query
                pass
            
            # Execute search (placeholder for vector search)
            # In production, use FT.SEARCH with vector similarity
            results = []
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    # JSON Operations
    def set_json(self, key: str, data: Dict, ttl: Optional[int] = None):
        """Store JSON data"""
        try:
            self.client.set(key, json.dumps(data), ex=ttl)
        except Exception as e:
            logger.error(f"Failed to set JSON: {e}")
            raise
    
    def get_json(self, key: str) -> Optional[Dict]:
        """Retrieve JSON data"""
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get JSON: {e}")
            return None
    
    # Cache Operations
    def cache_search_result(self, query_hash: str, results: List[Dict], ttl: int = None):
        """Cache search results"""
        ttl = ttl or settings.cache_ttl
        cache_key = f"cache:search:{query_hash}"
        
        cache_data = {
            "results": results,
            "timestamp": self._get_timestamp(),
            "ttl": ttl
        }
        
        self.set_json(cache_key, cache_data, ttl)
    
    def get_cached_search(self, query_hash: str) -> Optional[Dict]:
        """Retrieve cached search results"""
        cache_key = f"cache:search:{query_hash}"
        return self.get_json(cache_key)
    
    # Analytics
    def increment_counter(self, key: str, amount: int = 1):
        """Increment analytics counter"""
        return self.client.incr(key, amount)
    
    def get_stats(self) -> Dict:
        """Get Redis usage statistics"""
        try:
            info = self.client.info()
            return {
                "memory_used": info.get("used_memory_human", "0"),
                "total_keys": self.client.dbsize(),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    # Utility methods
    def _serialize_vector(self, vector: List[float]) -> str:
        """Serialize vector for Redis storage"""
        import struct
        return struct.pack(f'{len(vector)}f', *vector).hex()
    
    def _deserialize_vector(self, vector_str: str) -> List[float]:
        """Deserialize vector from Redis"""
        import struct
        vector_bytes = bytes.fromhex(vector_str)
        return list(struct.unpack(f'{len(vector_bytes)//4}f', vector_bytes))
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

# Global Redis client instance
redis_client = RedisClient()
