import openai
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
import hashlib
import json
import asyncio
from datetime import datetime
import time

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Generate and manage document embeddings"""
    
    def __init__(self):
        self.openai_client = None
        self.local_model = None
        self.embedding_cache = {}  # Simple in-memory cache
        
        # Initialize based on configuration
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize embedding providers"""
        try:
            # Debug: Log OpenAI API key status with more details
            import os
            env_openai_key = os.getenv('OPENAI_API_KEY')
            settings_openai_key = settings.openai_api_key
            
            logger.info(f"🔍 Environment OPENAI_API_KEY: {'present' if env_openai_key else 'missing'} (length: {len(env_openai_key) if env_openai_key else 0})")
            logger.info(f"🔍 Settings openai_api_key: {'present' if settings_openai_key else 'missing'} (length: {len(settings_openai_key) if settings_openai_key else 0})")
            
            if env_openai_key and settings_openai_key:
                logger.info(f"🔍 Keys match: {env_openai_key[:10] == settings_openai_key[:10]}")
            
            # Log first few characters for debugging (safe)
            if settings_openai_key:
                logger.info(f"🔍 OpenAI key starts with: {settings_openai_key[:10]}...")
            
            # Initialize OpenAI if API key is available
            if settings.openai_api_key:
                try:
                    # Use the most basic OpenAI client initialization to avoid version issues
                    logger.info("🔧 Attempting basic OpenAI client initialization...")
                    self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                    logger.info("✅ OpenAI client created successfully")
                    
                    # Test the client with a simple API call
                    try:
                        logger.info("🧪 Testing OpenAI API connection...")
                        test_response = self.openai_client.models.list()
                        logger.info(f"✅ OpenAI API test successful - found {len(test_response.data)} models")
                        logger.info("✅ OpenAI embedding service fully initialized and tested")
                    except Exception as test_error:
                        logger.error(f"❌ OpenAI API test failed: {test_error}")
                        logger.error(f"❌ API key may be invalid or there's a network/permission issue")
                        # Keep the client but mark it as potentially problematic
                        logger.warning("⚠️ OpenAI client created but API test failed - will attempt embeddings anyway")
                        
                except Exception as openai_error:
                    logger.error(f"❌ OpenAI client initialization failed: {openai_error}")
                    logger.error(f"❌ Error type: {type(openai_error).__name__}")
                    self.openai_client = None
            else:
                logger.warning("⚠️ OpenAI API key not found, using local models only")
            
            # Initialize local model as fallback
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    # Try to load the local model with better error handling
                    logger.info("💾 Attempting to load sentence-transformers model...")
                    self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("✅ Local embedding model loaded successfully (all-MiniLM-L6-v2)")
                except Exception as e:
                    logger.error(f"❌ Local model initialization failed: {e}")
                    logger.error(f"❌ Error type: {type(e).__name__}")
                    self.local_model = None
            else:
                logger.error("❌ sentence-transformers package not available - check Docker installation")
                logger.info("📝 To fix: ensure sentence-transformers is properly installed in production environment")
                
        except Exception as e:
            logger.error(f"Embedding service initialization failed: {e}")
    
    async def generate_embedding(self, text: str, method: str = "auto") -> Dict:
        """Generate embedding for text"""
        try:
            # Clean and prepare text
            clean_text = self._prepare_text(text)
            
            # Check cache first
            cache_key = self._get_cache_key(clean_text, method)
            if cache_key in self.embedding_cache:
                logger.debug("Cache hit for embedding")
                return self.embedding_cache[cache_key]
            
            # Generate embedding based on method with proper availability checking
            if method == "auto":
                if self.openai_client:
                    method = "openai"
                    logger.debug("🤖 Auto-selected OpenAI embedding method")
                elif self.local_model:
                    method = "local"
                    logger.debug("💻 Auto-selected local embedding method")
                else:
                    available_methods = []
                    if self.openai_client:
                        available_methods.append("openai")
                    if self.local_model:
                        available_methods.append("local")
                    raise ValueError(f"No embedding methods available. OpenAI client: {self.openai_client is not None}, Local model: {self.local_model is not None}. Available: {available_methods}")
            
            start_time = time.time()
            
            if method == "openai":
                if not self.openai_client:
                    raise ValueError(f"OpenAI embedding method requested but OpenAI client not available")
                result = await self._generate_openai_embedding(clean_text)
            elif method == "local":
                if not self.local_model:
                    raise ValueError(f"Local embedding method requested but local model not available")
                result = await self._generate_local_embedding(clean_text)
            else:
                raise ValueError(f"Unknown embedding method '{method}'. Available methods: openai, local")
            
            generation_time = time.time() - start_time
            
            # Add metadata
            result.update({
                "method": method,
                "generation_time": generation_time,
                "text_length": len(clean_text),
                "cache_key": cache_key
            })
            
            # Cache result
            self.embedding_cache[cache_key] = result
            
            logger.debug(f"Generated embedding: {method}, {len(result['vector'])}D, {generation_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def generate_batch_embeddings(self, texts: List[str], method: str = "auto", batch_size: int = 10) -> List[Dict]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            results = []
            
            # Process in batches to avoid rate limits
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                # Generate embeddings for batch
                if method == "openai" and self.openai_client:
                    batch_results = await self._generate_openai_batch(batch)
                elif method == "local" and self.local_model:
                    batch_results = await self._generate_local_batch(batch)
                else:
                    # Fallback to individual generation
                    batch_results = []
                    for text in batch:
                        result = await self.generate_embedding(text, method)
                        batch_results.append(result)
                
                results.extend(batch_results)
                
                # Small delay to respect rate limits
                if method == "openai":
                    await asyncio.sleep(0.1)
            
            logger.info(f"Generated {len(results)} embeddings in batches")
            return results
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise
    
    async def _generate_openai_embedding(self, text: str) -> Dict:
        """Generate OpenAI embedding"""
        try:
            # Use the exact API format from OpenAI documentation
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=settings.embedding_model,
                input=text
                # Note: dimensions parameter removed - let OpenAI use default dimensions
                # The text-embedding-3-small model has 1536 dimensions by default
            )
            
            return {
                "vector": response.data[0].embedding,
                "model": settings.embedding_model,
                "dimensions": len(response.data[0].embedding),
                "usage": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def _generate_openai_batch(self, texts: List[str]) -> List[Dict]:
        """Generate OpenAI embeddings in batch"""
        try:
            # Use the exact API format from OpenAI documentation for batch processing
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=settings.embedding_model,
                input=texts
                # Note: dimensions parameter removed - let OpenAI use default dimensions
            )
            
            results = []
            for i, embedding_data in enumerate(response.data):
                results.append({
                    "vector": embedding_data.embedding,
                    "model": settings.embedding_model,
                    "dimensions": len(embedding_data.embedding),
                    "usage": response.usage.total_tokens // len(texts) if hasattr(response, 'usage') else None,
                    "batch_index": i
                })
            
            return results
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            raise
    
    async def _generate_local_embedding(self, text: str) -> Dict:
        """Generate local embedding using SentenceTransformers"""
        try:
            # Run in thread to avoid blocking
            vector = await asyncio.to_thread(
                self.local_model.encode,
                text,
                normalize_embeddings=True
            )
            
            return {
                "vector": vector.tolist(),
                "model": "all-MiniLM-L6-v2",
                "dimensions": len(vector),
                "usage": None
            }
            
        except Exception as e:
            logger.error(f"Local embedding failed: {e}")
            raise
    
    async def _generate_local_batch(self, texts: List[str]) -> List[Dict]:
        """Generate local embeddings in batch"""
        try:
            vectors = await asyncio.to_thread(
                self.local_model.encode,
                texts,
                normalize_embeddings=True,
                batch_size=32
            )
            
            results = []
            for i, vector in enumerate(vectors):
                results.append({
                    "vector": vector.tolist(),
                    "model": "all-MiniLM-L6-v2", 
                    "dimensions": len(vector),
                    "usage": None,
                    "batch_index": i
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Local batch embedding failed: {e}")
            raise
    
    def _prepare_text(self, text: str, max_length: int = 8192) -> str:
        """Prepare text for embedding generation"""
        # Remove excessive whitespace
        clean_text = ' '.join(text.split())
        
        # Truncate if too long (OpenAI has token limits)
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."
            logger.debug(f"Text truncated to {max_length} characters")
        
        return clean_text
    
    def _get_cache_key(self, text: str, method: str) -> str:
        """Generate cache key for embedding"""
        content = f"{method}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        try:
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Cosine similarity
            dot_product = np.dot(v1, v2)
            norms = np.linalg.norm(v1) * np.linalg.norm(v2)
            
            if norms == 0:
                return 0.0
            
            similarity = dot_product / norms
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def get_embedding_stats(self) -> Dict:
        """Get embedding service statistics"""
        # Determine default method based on availability
        if self.openai_client:
            default_method = "openai"
        elif self.local_model:
            default_method = "local"
        else:
            default_method = "none_available"
            
        return {
            "cache_size": len(self.embedding_cache),
            "openai_available": self.openai_client is not None,
            "local_model_available": self.local_model is not None,
            "default_method": default_method
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")

# Global instance
embedding_service = EmbeddingService()
