# DocuMind - Technical Setup Guide

## 🚀 Quick Start Checklist

- [ ] Redis Cloud account setup
- [ ] Python environment configuration
- [ ] Project structure creation
- [ ] Redis connection testing
- [ ] Environment variables configuration
- [ ] Basic API server running

## 🏗️ Project Structure

```
documind/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration management
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py  # Redis connection & operations
│   │   │   └── models.py        # Data models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py     # Document endpoints
│   │   │   ├── search.py        # Search endpoints
│   │   │   └── analytics.py     # Analytics endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── embedding_service.py
│   │   │   └── search_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_handlers.py
│   │       └── cache.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   ├── package.json
│   └── README.md
├── docs/
│   ├── api.md
│   ├── deployment.md
│   └── demo-script.md
├── tests/
│   ├── backend/
│   └── frontend/
├── scripts/
│   ├── setup_redis.py
│   ├── load_demo_data.py
│   └── benchmark.py
├── .gitignore
├── docker-compose.yml       # Optional: local Redis for development
└── README.md
```

## 🔧 Redis Cloud Setup

### Step 1: Create Redis Cloud Account
1. Go to [Redis Cloud](https://redis.io/try-free/)
2. Sign up for free account
3. Create new subscription → **Essentials** → **30MB Free**
4. Choose **Redis Stack** (includes Vector Search)
5. Note your connection details

### Step 2: Get Connection Details
```bash
# From Redis Cloud Console, you'll get:
Endpoint: redis-12345.c123.us-east-1-1.ec2.cloud.redislabs.com:12345
Password: your-redis-password
```

### Step 3: Test Connection
```bash
# Install Redis CLI (optional)
pip install redis-cli

# Test connection
redis-cli -h your-endpoint -p your-port -a your-password ping
# Should return: PONG
```

## 🐍 Python Backend Setup

### Step 1: Environment Setup
```bash
# Create project directory
mkdir documind && cd documind
mkdir backend && cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies
```bash
# Create requirements.txt
pip install fastapi uvicorn redis python-multipart
pip install openai sentence-transformers PyPDF2 python-docx
pip install python-dotenv pydantic-settings numpy
pip freeze > requirements.txt
```

### Step 3: Configuration Management
Create `app/config.py`:
```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_decode_responses: bool = True
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # OpenAI Configuration (optional)
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = {".pdf", ".txt", ".docx"}
    upload_dir: str = "uploads"
    
    # Cache Configuration
    cache_ttl: int = 3600  # 1 hour
    max_search_results: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### Step 4: Redis Client Setup
Create `app/database/redis_client.py`:
```python
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
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                ssl=settings.redis_ssl,
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
```

### Step 5: FastAPI Application Setup
Create `app/main.py`:
```python
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
```

### Step 6: Environment Configuration
Create `.env.example`:
```bash
# Redis Configuration
REDIS_HOST=your-redis-endpoint.com
REDIS_PORT=12345
REDIS_PASSWORD=your-redis-password
REDIS_SSL=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# OpenAI (Optional - can use local models)
OPENAI_API_KEY=your-openai-api-key

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads

# Cache Settings
CACHE_TTL=3600
```

Copy to `.env` and fill in your actual Redis credentials.

## 🧪 Testing the Setup

### Step 1: Run the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "redis": "connected",
  "version": "1.0.0"
}

# Redis stats
curl http://localhost:8000/api/stats

# Test endpoint
curl http://localhost:8000/api/test
```

### Step 3: Create Test Script
Create `scripts/test_setup.py`:
```python
import requests
import sys

def test_api():
    """Test API endpoints"""
    base_url = "http://localhost:8000"
    
    tests = [
        ("Health Check", f"{base_url}/health"),
        ("Test Endpoint", f"{base_url}/api/test"),
        ("Redis Stats", f"{base_url}/api/stats")
    ]
    
    print("🧪 Testing DocuMind API Setup...")
    print("=" * 50)
    
    all_passed = True
    
    for test_name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {test_name}: PASSED")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ {test_name}: FAILED (Status: {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name}: FAILED (Error: {e})")
            all_passed = False
        
        print()
    
    if all_passed:
        print("🎉 All tests passed! Setup is complete.")
        return True
    else:
        print("❌ Some tests failed. Check configuration.")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
```

## 🐳 Optional: Docker Development Setup

If you prefer Docker or want to test locally without Redis Cloud:

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight UI
    environment:
      - REDIS_ARGS=--requirepass yourpassword
    volumes:
      - redis_data:/data

  api:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=yourpassword
    depends_on:
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  redis_data:
```

## 🔍 Troubleshooting

### Common Issues

**1. Redis Connection Failed**
- Verify endpoint, port, and password
- Check if Redis Cloud instance is running
- Ensure SSL settings match your configuration

**2. Import Errors**
- Activate virtual environment: `source venv/bin/activate`
- Install missing packages: `pip install -r requirements.txt`
- Check Python path: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

**3. Port Already in Use**
- Kill existing process: `lsof -ti:8000 | xargs kill -9`
- Use different port: `uvicorn app.main:app --port 8001`

**4. SSL Certificate Issues**
- Update Redis connection: `redis_ssl_cert_reqs=None`
- Check Redis Cloud SSL requirements

### Debug Commands
```bash
# Check Redis connection manually
python -c "
import redis
r = redis.Redis(host='your-host', port=12345, password='your-pass', ssl=True)
print('PING:', r.ping())
print('INFO:', r.info()['redis_version'])
"

# Test specific Redis commands
redis-cli -h your-host -p 12345 -a your-password --tls INFO memory

# Check Python imports
python -c "import redis; import fastapi; print('✅ All imports working')"
```

## ✅ Setup Complete!

Once all tests pass, you have:
- ✅ Redis Cloud connection established
- ✅ FastAPI server running
- ✅ Project structure in place
- ✅ Configuration management ready
- ✅ Basic API endpoints working
- ✅ Redis client with vector search foundation

**Next Steps:**
1. Document processing pipeline implementation
2. Embedding service integration
3. Vector search functionality
4. Frontend development

Your foundation is now solid for building the semantic document cache! 🚀