import redis
import ssl
import socket
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not RedisClient._initialized:
            self.client: Optional[redis.Redis] = None
            self._connected = False
            RedisClient._initialized = True
    
    def connect(self):
        """Establish Redis connection using IP to avoid IDNA issues"""
        if self._connected:
            return
            
        try:
            # Use IP address instead of hostname to avoid IDNA encoding issues
            redis_host = "23.22.188.206"  # Your Redis Cloud IP
            redis_port = int(settings.redis_port)
            redis_password = settings.redis_password
            
            logger.info(f"Connecting to Redis Cloud at {redis_host}:{redis_port}")
            
            
            # Connect using IP address with SSL and improved settings for concurrency
            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                ssl=True,
                ssl_cert_reqs=None,
                ssl_check_hostname=False,
                decode_responses=True,
                socket_connect_timeout=15,
                socket_timeout=15,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=20,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            self.client.ping()
            self._connected = True
            logger.info(f"✅ Redis connected successfully to {redis_host}:{redis_port}")
            return
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            # Try fallback connection
            self._try_fallback_connection()
    
    def _try_fallback_connection(self):
        """Fallback connection method"""
        try:
            # Alternative approach using redis.from_url with IP
            redis_url = f"rediss://default:{settings.redis_password}@23.22.188.206:{settings.redis_port}"
            
            logger.info("Attempting fallback Redis connection...")
            
            self.client = redis.from_url(
                redis_url,
                ssl_cert_reqs=None,
                ssl_check_hostname=False,
                decode_responses=True,
                socket_connect_timeout=15,
                socket_timeout=15
            )
            
            self.client.ping()
            self._connected = True
            logger.info("✅ Redis fallback connection successful")
            
        except Exception as e:
            logger.error(f"❌ Redis fallback connection failed: {e}")
            # Create mock client for development
            self.client = EnhancedMockRedisClient()
            self._connected = False
            logger.warning("⚠️ Using enhanced mock Redis client for development")
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            if not self._connected:
                self.connect()
            if self.client:
                return self.client.ping()
            return False
        except:
            return False
    
    # Vector Operations (Redis Stack)
    def create_vector_index(self, index_name: str, schema: Dict):
        """Create vector search index"""
        try:
            from redis.commands.search.field import VectorField, TextField, NumericField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            if not self._connected:
                self.connect()
            if not self.client:
                raise Exception("Redis client not connected")
                
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
            if not self._connected:
                self.connect()
            if not self.client:
                raise Exception("Redis client not connected")
                
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
    
    def search_vectors(self, query_vector: List[float], limit: int = 10, filters: Optional[Dict] = None):
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
            if not self._connected:
                self.connect()
            if not self.client:
                raise Exception("Redis client not connected")
            self.client.set(key, json.dumps(data), ex=ttl)
        except Exception as e:
            logger.error(f"Failed to set JSON: {e}")
            raise
    
    def get_json(self, key: str) -> Optional[Dict]:
        """Retrieve JSON data"""
        try:
            if not self._connected:
                self.connect()
            if not self.client:
                return None
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get JSON: {e}")
            return None
    
    # Cache Operations
    def cache_search_result(self, query_hash: str, results: List[Dict], ttl: Optional[int] = None):
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
        if not self._connected:
            self.connect()
        if not self.client:
            return 0
        return self.client.incr(key, amount)
    
    def get_stats(self) -> Dict:
        """Get Redis usage statistics"""
        try:
            if not self._connected:
                self.connect()
            if not self.client:
                return {}
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

class MockRedisClient:
    """Mock Redis client for development when connection fails"""
    
    def __init__(self):
        self._data = {}
        self._sets = {}
    
    def ping(self):
        return True
    
    def set(self, key, value, ex=None):
        self._data[key] = value
        return True
    
    def get(self, key):
        return self._data.get(key)
    
    def hset(self, key, mapping=None, **kwargs):
        if key not in self._data:
            self._data[key] = {}
        if mapping:
            self._data[key].update(mapping)
        self._data[key].update(kwargs)
        return True
    
    def hgetall(self, key):
        return self._data.get(key, {})
    
    def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)
        return len(keys)
    
    def sadd(self, key, *values):
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].update(values)
        return len(values)
    
    def scard(self, key):
        return len(self._sets.get(key, set()))
    
    def smembers(self, key):
        return self._sets.get(key, set())
    
    def srem(self, key, *values):
        if key in self._sets:
            self._sets[key].discard(*values)
        return len(values)
    
    def incr(self, key, amount=1):
        current = int(self._data.get(key, 0))
        new_value = current + amount
        self._data[key] = str(new_value)
        return new_value
    
    def dbsize(self):
        return len(self._data)
    
    def info(self):
        return {
            "used_memory_human": "1.5M",
            "connected_clients": 1,
            "total_commands_processed": 1000
        }
    
    def keys(self, pattern="*"):
        return list(self._data.keys())
    
    def time(self):
        import time
        return [int(time.time()), 0]


class EnhancedMockRedisClient(MockRedisClient):
    """Enhanced mock with vector search simulation"""
    
    def __init__(self):
        super().__init__()
        self._vectors = {}
        if not hasattr(self, '_sorted_sets'):
            self._sorted_sets = {}
        if not hasattr(self, '_lists'):
            self._lists = {}
        logger.info("🔧 Using enhanced mock Redis for demo")
    
    def zadd(self, key, mapping):
        """Add to sorted set"""
        if key not in self._sorted_sets:
            self._sorted_sets[key] = {}
        self._sorted_sets[key].update(mapping)
        return len(mapping)
    
    def zcard(self, key):
        """Get sorted set cardinality"""
        return len(self._sorted_sets.get(key, {}))
    
    def lpush(self, key, *values):
        """Push to list"""
        if key not in self._lists:
            self._lists[key] = []
        for value in reversed(values):
            self._lists[key].insert(0, value)
        return len(self._lists[key])
    
    def llen(self, key):
        """Get list length"""
        return len(self._lists.get(key, []))
    
    def ltrim(self, key, start, end):
        """Trim list"""
        if key in self._lists:
            self._lists[key] = self._lists[key][start:end+1]
        return True
    
    def ft(self, index_name):
        """Mock Redis Search"""
        return MockSearchIndex()
    
    def vector_search(self, query_vector, limit=10):
        """Mock vector search with random similarity scores"""
        import random
        results = []
        
        for i in range(min(limit, 5)):  # Return up to 5 mock results
            results.append({
                "chunk_id": f"mock_chunk_{i}",
                "doc_id": f"mock_doc_{i}",
                "content": f"This is mock search result {i+1} for demonstration purposes.",
                "similarity_score": random.uniform(0.7, 0.95),
                "title": f"Mock Document {i+1}",
                "filename": f"demo_file_{i+1}.pdf"
            })
        
        return results
    
    def incrby(self, key: str, amount: int) -> int:
        """Increment counter by amount"""
        current = int(self._data.get(key, 0))
        new_value = current + amount
        self._data[key] = str(new_value)
        return new_value
    
    def decrby(self, key: str, amount: int) -> int:
        """Decrement counter by amount"""
        current = int(self._data.get(key, 0))
        new_value = current - amount
        self._data[key] = str(new_value)
        return new_value
    
    def decr(self, key: str) -> int:
        """Decrement counter"""
        current = int(self._data.get(key, 0))
        new_value = current - 1
        self._data[key] = str(new_value)
        return new_value


class MockSearchIndex:
    def create_index(self, schema, definition=None):
        logger.info("🔧 Mock search index created")
        return True
    
    def search(self, query, query_params=None):
        logger.info(f"🔧 Mock search executed: {query}")
        return MockSearchResult()
    
    def info(self):
        return {"num_docs": 5, "indexing": False}


class MockSearchResult:
    def __init__(self):
        self.docs = [MockDoc(i) for i in range(3)]


class MockDoc:
    def __init__(self, i):
        self.id = f"vector:mock_chunk_{i}"
        self.score = 0.8 + (i * 0.05)
        self.chunk_id = f"mock_chunk_{i}"
        self.content = f"Mock content {i+1}"
        self.doc_id = f"mock_doc_{i}"


    async def execute_with_retry(self, operation, *args, max_retries=3, **kwargs):
        """Execute Redis operation with retry logic"""
        for attempt in range(max_retries):
            try:
                if not self._connected:
                    self.connect()
                return await asyncio.to_thread(operation, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Redis operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
    
    def set_json_with_retry(self, key: str, data: Dict, ttl: Optional[int] = None):
        """Store JSON data with retry logic"""
        return asyncio.create_task(
            self.execute_with_retry(self.client.set, key, json.dumps(data), ex=ttl)
        )

# Global Redis client instance
redis_client = RedisClient()
