#!/usr/bin/env python3
"""
Redis setup and initialization script
"""
import sys
import os
import logging
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database.redis_client import redis_client
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection() -> bool:
    """Test basic Redis connection"""
    try:
        result = redis_client.health_check()
        if result:
            logger.info("✅ Redis connection successful")
            return True
        else:
            logger.error("❌ Redis connection failed")
            return False
    except Exception as e:
        logger.error(f"❌ Redis connection error: {e}")
        return False

def initialize_counters() -> bool:
    """Initialize analytics counters"""
    try:
        counters = [
            "stats:total_documents",
            "stats:total_searches", 
            "stats:cache_hits"
        ]
        
        for counter in counters:
            if not redis_client.client.exists(counter):
                redis_client.client.set(counter, 0)
                logger.info(f"Initialized counter: {counter}")
        
        logger.info("✅ Analytics counters initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Counter initialization failed: {e}")
        return False

def create_vector_index() -> bool:
    """Create vector search index for documents"""
    try:
        # This is a placeholder for vector index creation
        # In production, you would create the actual Redis Stack vector index here
        
        index_name = "document_vectors"
        logger.info(f"Vector index '{index_name}' setup placeholder - implement with Redis Stack")
        
        # Example schema for when Redis Stack is fully configured:
        # from redis.commands.search.field import VectorField, TextField
        # from redis.commands.search.indexDefinition import IndexDefinition, IndexType
        # 
        # schema = [
        #     TextField("document_id"),
        #     TextField("filename"),
        #     TextField("content"),
        #     VectorField("embedding", "HNSW", {
        #         "TYPE": "FLOAT32",
        #         "DIM": settings.embedding_dimensions,
        #         "DISTANCE_METRIC": "COSINE"
        #     })
        # ]
        # 
        # redis_client.create_vector_index(index_name, schema)
        
        logger.info("✅ Vector index setup completed (placeholder)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector index creation failed: {e}")
        return False

def setup_sample_data() -> bool:
    """Setup sample configuration data"""
    try:
        # Set up some sample popular queries
        sample_queries = [
            "machine learning",
            "data science",
            "artificial intelligence",
            "python programming",
            "database design"
        ]
        
        for i, query in enumerate(sample_queries):
            redis_client.client.zadd("stats:popular_queries", {query: len(sample_queries) - i})
        
        logger.info("✅ Sample data setup completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample data setup failed: {e}")
        return False

def verify_setup() -> Dict[str, Any]:
    """Verify the Redis setup"""
    try:
        verification_results = {
            "connection": test_redis_connection(),
            "counters": bool(redis_client.client.exists("stats:total_documents")),
            "redis_info": redis_client.get_stats(),
            "configuration": {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "ssl": settings.redis_ssl,
                "embedding_dimensions": settings.embedding_dimensions
            }
        }
        
        return verification_results
        
    except Exception as e:
        logger.error(f"❌ Setup verification failed: {e}")
        return {"error": str(e)}

def main():
    """Main setup function"""
    print("🚀 DocuMind Redis Setup")
    print("=" * 50)
    
    # Test connection first
    print("\n1. Testing Redis connection...")
    if not test_redis_connection():
        print("❌ Setup failed: Cannot connect to Redis")
        sys.exit(1)
    
    # Initialize counters
    print("\n2. Initializing analytics counters...")
    if not initialize_counters():
        print("⚠️  Warning: Counter initialization failed")
    
    # Create vector index
    print("\n3. Setting up vector search index...")
    if not create_vector_index():
        print("⚠️  Warning: Vector index setup failed")
    
    # Setup sample data
    print("\n4. Setting up sample data...")
    if not setup_sample_data():
        print("⚠️  Warning: Sample data setup failed")
    
    # Verify setup
    print("\n5. Verifying setup...")
    verification = verify_setup()
    
    print("\n📊 Setup Verification Results:")
    print("-" * 30)
    for key, value in verification.items():
        if key == "redis_info":
            print(f"Redis Info:")
            for info_key, info_value in value.items():
                print(f"  {info_key}: {info_value}")
        elif key == "configuration":
            print(f"Configuration:")
            for config_key, config_value in value.items():
                print(f"  {config_key}: {config_value}")
        else:
            status = "✅" if value else "❌"
            print(f"{status} {key}: {value}")
    
    print("\n🎉 Redis setup completed!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: python -m app.main")
    print("2. Test the API endpoints: http://localhost:8000/docs")
    print("3. Upload documents and test search functionality")

if __name__ == "__main__":
    main()
