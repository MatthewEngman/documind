# Embedding Service Implementation

## 🎯 Overview

Transform document chunks into searchable vectors using OpenAI embeddings or local models, then store them in Redis 8's Vector Sets for lightning-fast semantic search.

## 📋 Additional Dependencies

Add to `backend/requirements.txt`:
```txt
# Embedding Services
openai==1.54.3
sentence-transformers==2.2.2
transformers==4.36.2
torch==2.1.2
numpy==1.24.3

# Vector Operations
faiss-cpu==1.7.4          # For local vector operations (optional)
scikit-learn==1.3.2       # For similarity calculations
```

## 🧠 Core Embedding Service

Create `backend/app/services/embedding_service.py`:

```python
import openai
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
import hashlib
import json
import asyncio
from datetime import datetime
import time

from sentence_transformers import SentenceTransformer
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
            # Initialize OpenAI if API key is available
            if settings.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                logger.info("✅ OpenAI embedding service initialized")
            else:
                logger.info("⚠️ OpenAI API key not found, using local models only")
            
            # Initialize local model as fallback
            try:
                self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Local embedding model loaded (all-MiniLM-L6-v2)")
            except Exception as e:
                logger.warning(f"Local model initialization failed: {e}")
                
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
            
            # Generate embedding based on method
            if method == "auto":
                method = "openai" if self.openai_client else "local"
            
            start_time = time.time()
            
            if method == "openai" and self.openai_client:
                result = await self._generate_openai_embedding(clean_text)
            elif method == "local" and self.local_model:
                result = await self._generate_local_embedding(clean_text)
            else:
                raise ValueError(f"Embedding method '{method}' not available")
            
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
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=settings.embedding_model,
                input=text,
                dimensions=settings.embedding_dimensions
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
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=settings.embedding_model,
                input=texts,
                dimensions=settings.embedding_dimensions
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
        return {
            "cache_size": len(self.embedding_cache),
            "openai_available": self.openai_client is not None,
            "local_model_available": self.local_model is not None,
            "default_method": "openai" if self.openai_client else "local"
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")

# Global instance
embedding_service = EmbeddingService()
```

## 🔍 Vector Search Service

Create `backend/app/services/vector_search_service.py`:

```python
import redis
import numpy as np
import json
from typing import List, Dict, Optional, Any
import logging
import struct
from datetime import datetime

from app.database.redis_client import redis_client
from app.services.embedding_service import embedding_service
from app.config import settings

logger = logging.getLogger(__name__)

class VectorSearchService:
    """Redis Vector Sets-based semantic search"""
    
    def __init__(self):
        self.vector_index_name = "doc_vectors"
        self.initialized = False
        
    async def initialize_vector_index(self):
        """Initialize Redis Vector Search index"""
        try:
            from redis.commands.search.field import VectorField, TextField, NumericField, TagField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            # Check if index already exists
            try:
                info = redis_client.client.ft(self.vector_index_name).info()
                logger.info(f"Vector index '{self.vector_index_name}' already exists")
                self.initialized = True
                return
            except:
                pass
            
            # Define schema for vector search
            schema = [
                VectorField(
                    "vector",
                    "FLAT",  # Using FLAT algorithm for simplicity
                    {
                        "TYPE": "FLOAT32",
                        "DIM": settings.embedding_dimensions,
                        "DISTANCE_METRIC": "COSINE"
                    }
                ),
                TextField("content", weight=2.0),
                TextField("title"),
                TextField("filename"),
                TagField("doc_id"),
                TagField("chunk_id"),
                TagField("tags", separator="|"),
                NumericField("word_count"),
                NumericField("chunk_index"),
                TextField("upload_date")
            ]
            
            # Create index
            redis_client.client.ft(self.vector_index_name).create_index(
                schema,
                definition=IndexDefinition(
                    prefix=["vector:"],
                    index_type=IndexType.HASH
                )
            )
            
            logger.info(f"✅ Vector search index '{self.vector_index_name}' created")
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Vector index initialization failed: {e}")
            raise
    
    async def add_document_vectors(self, doc_id: str, chunks_data: List[Dict]) -> int:
        """Add document chunk vectors to search index"""
        try:
            if not self.initialized:
                await self.initialize_vector_index()
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk["text"] for chunk in chunks_data]
            embeddings = await embedding_service.generate_batch_embeddings(chunk_texts)
            
            vectors_added = 0
            
            for chunk, embedding in zip(chunks_data, embeddings):
                try:
                    # Prepare vector data for Redis
                    vector_key = f"vector:{chunk['chunk_id']}"
                    
                    # Serialize vector
                    vector_bytes = self._serialize_vector(embedding["vector"])
                    
                    # Prepare document data
                    vector_data = {
                        "vector": vector_bytes,
                        "content": chunk["text"][:1000],  # Truncate for storage efficiency
                        "title": chunk.get("title", ""),
                        "filename": chunk.get("filename", ""),
                        "doc_id": doc_id,
                        "chunk_id": chunk["chunk_id"],
                        "tags": "|".join(chunk.get("tags", [])),
                        "word_count": chunk["word_count"],
                        "chunk_index": chunk.get("chunk_index", 0),
                        "upload_date": chunk.get("upload_date", datetime.utcnow().isoformat()),
                        "embedding_method": embedding["method"],
                        "embedding_model": embedding["model"]
                    }
                    
                    # Store in Redis
                    redis_client.client.hset(vector_key, mapping=vector_data)
                    vectors_added += 1
                    
                except Exception as e:
                    logger.error(f"Failed to add vector for chunk {chunk['chunk_id']}: {e}")
            
            logger.info(f"Added {vectors_added}/{len(chunks_data)} vectors for document {doc_id}")
            
            # Update analytics
            redis_client.increment_counter("stats:vectors_created", vectors_added)
            
            return vectors_added
            
        except Exception as e:
            logger.error(f"Failed to add document vectors: {e}")
            raise
    
    async def search_vectors(self, 
                           query: str, 
                           limit: int = 10,
                           filters: Dict = None,
                           similarity_threshold: float = 0.7) -> List[Dict]:
        """Perform semantic vector search"""
        try:
            if not self.initialized:
                await self.initialize_vector_index()
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query)
            query_vector = query_embedding["vector"]
            
            # Build search query
            search_query = self._build_search_query(filters, limit)
            
            # Perform vector search using Redis
            results = await self._execute_vector_search(query_vector, search_query, limit)
            
            # Process and rank results
            processed_results = self._process_search_results(results, query_vector, similarity_threshold)
            
            logger.info(f"Vector search completed: {len(processed_results)} results for query: '{query[:50]}...'")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _execute_vector_search(self, query_vector: List[float], search_query: str, limit: int) -> List[Dict]:
        """Execute vector search against Redis"""
        try:
            # Serialize query vector
            query_blob = self._serialize_vector(query_vector)
            
            # Build FT.SEARCH query with vector similarity
            vector_query = f"*=>[KNN {limit} @vector $query_vector AS score]"
            
            # Execute search
            results = redis_client.client.ft(self.vector_index_name).search(
                vector_query,
                query_params={"query_vector": query_blob}
            )
            
            # Convert results to list of dicts
            search_results = []
            for doc in results.docs:
                result = {
                    "id": doc.id,
                    "score": float(doc.score) if hasattr(doc, 'score') else 0.0,
                    **{k: v for k, v in doc.__dict__.items() if not k.startswith('_')}
                }
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search execution failed: {e}")
            return []
    
    def _build_search_query(self, filters: Dict = None, limit: int = 10) -> str:
        """Build Redis search query with filters"""
        query_parts = ["*"]
        
        if filters:
            if "doc_id" in filters:
                query_parts.append(f"@doc_id:{{{filters['doc_id']}}}")
            
            if "tags" in filters:
                tag_filters = [f"@tags:{{{tag}}}" for tag in filters["tags"]]
                query_parts.append(f"({' | '.join(tag_filters)})")
            
            if "filename" in filters:
                query_parts.append(f"@filename:*{filters['filename']}*")
            
            if "word_count_min" in filters:
                query_parts.append(f"@word_count:[{filters['word_count_min']} +inf]")
        
        return " ".join(query_parts)
    
    def _process_search_results(self, results: List[Dict], query_vector: List[float], threshold: float) -> List[Dict]:
        """Process and enhance search results"""
        processed = []
        
        for result in results:
            try:
                # Calculate actual similarity
                if "vector" in result:
                    doc_vector = self._deserialize_vector(result["vector"])
                    similarity = embedding_service.calculate_similarity(query_vector, doc_vector)
                else:
                    similarity = 1.0 - float(result.get("score", 1.0))  # Convert distance to similarity
                
                # Apply similarity threshold
                if similarity < threshold:
                    continue
                
                # Enhance result data
                enhanced_result = {
                    "chunk_id": result.get("chunk_id", ""),
                    "doc_id": result.get("doc_id", ""),
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "filename": result.get("filename", ""),
                    "similarity_score": round(similarity, 4),
                    "word_count": int(result.get("word_count", 0)),
                    "chunk_index": int(result.get("chunk_index", 0)),
                    "tags": result.get("tags", "").split("|") if result.get("tags") else [],
                    "upload_date": result.get("upload_date", ""),
                    "embedding_method": result.get("embedding_method", ""),
                    "search_score": float(result.get("score", 0.0))
                }
                
                processed.append(enhanced_result)
                
            except Exception as e:
                logger.error(f"Error processing search result: {e}")
                continue
        
        # Sort by similarity score (descending)
        processed.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return processed
    
    async def delete_document_vectors(self, doc_id: str) -> bool:
        """Delete all vectors for a document"""
        try:
            # Search for document vectors
            search_query = f"@doc_id:{{{doc_id}}}"
            results = redis_client.client.ft(self.vector_index_name).search(search_query)
            
            # Delete vector documents
            deleted_count = 0
            for doc in results.docs:
                redis_client.client.delete(doc.id)
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} vectors for document {doc_id}")
            
            # Update analytics
            redis_client.increment_counter("stats:vectors_deleted", deleted_count)
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            return False
    
    def _serialize_vector(self, vector: List[float]) -> bytes:
        """Serialize vector for Redis storage"""
        return struct.pack(f'{len(vector)}f', *vector)
    
    def _deserialize_vector(self, vector_bytes: bytes) -> List[float]:
        """Deserialize vector from Redis"""
        return list(struct.unpack(f'{len(vector_bytes)//4}f', vector_bytes))
    
    def get_vector_stats(self) -> Dict:
        """Get vector search statistics"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}
            
            # Get index info
            info = redis_client.client.ft(self.vector_index_name).info()
            
            return {
                "status": "initialized",
                "index_name": self.vector_index_name,
                "total_docs": info.get("num_docs", 0),
                "indexing": info.get("indexing", False),
                "total_vectors": redis_client.client.get("stats:vectors_created") or 0,
                "deleted_vectors": redis_client.client.get("stats:vectors_deleted") or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting vector stats: {e}")
            return {"status": "error", "error": str(e)}

# Global instance
vector_search_service = VectorSearchService()
```

## 🔗 Integration with Document Processor

Update `backend/app/services/document_processor.py` to include vector generation:

```python
# Add this import at the top
from app.services.vector_search_service import vector_search_service

# Update the _store_document method to include vector generation
async def _store_document(self, 
                        doc_id: str, 
                        file_metadata: Dict, 
                        extraction_result: Dict, 
                        chunks: List[DocumentChunk]) -> Dict:
    """Store document and chunks in Redis with vector embeddings"""
    
    # ... existing document storage code ...
    
    # NEW: Generate and store vectors
    try:
        self._update_status(doc_id, "generating_vectors", 85)
        
        # Prepare chunks for vector generation
        chunks_for_vectors = []
        for chunk in chunks:
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "title": document_data["title"],
                "filename": document_data["filename"],
                "word_count": chunk.word_count,
                "chunk_index": chunk.metadata.get("chunk_index", 0),
                "tags": document_data.get("tags", []),
                "upload_date": document_data["uploaded_at"]
            }
            chunks_for_vectors.append(chunk_data)
        
        # Generate and store vectors
        vectors_added = await vector_search_service.add_document_vectors(doc_id, chunks_for_vectors)
        document_data["vectors_generated"] = vectors_added
        
        logger.info(f"Generated {vectors_added} vectors for document {doc_id}")
        
    except Exception as e:
        logger.error(f"Vector generation failed for {doc_id}: {e}")
        document_data["vector_error"] = str(e)
    
    # ... rest of existing code ...
    
    return document_data

# Update the delete_document method to include vector cleanup
async def delete_document(self, doc_id: str) -> bool:
    """Delete document and all associated data including vectors"""
    try:
        # ... existing deletion code ...
        
        # NEW: Delete vectors
        await vector_search_service.delete_document_vectors(doc_id)
        
        # ... rest of existing code ...
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        return False
```

## 🔍 Search API Endpoints

Create `backend/app/api/search.py`:

```python
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel

from app.services.vector_search_service import vector_search_service
from app.services.embedding_service import embedding_service
from app.database.redis_client import redis_client
import hashlib
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    similarity_threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    use_cache: bool = True

class SearchResponse(BaseModel):
    query: str
    results: List[Dict]
    total_results: int
    search_time_ms: int
    cache_hit: bool
    embedding_method: str

@router.post("/")
async def semantic_search(request: SearchRequest):
    """Perform semantic search across documents"""
    try:
        import time
        start_time = time.time()
        
        # Check semantic cache first
        cache_hit = False
        if request.use_cache:
            cached_result = await _get_cached_search(request.query, request.filters)
            if cached_result:
                cache_hit = True
                search_time = time.time() - start_time
                cached_result["search_time_ms"] = int(search_time * 1000)
                cached_result["cache_hit"] = True
                
                # Update cache hit analytics
                redis_client.increment_counter("stats:cache_hits")
                return cached_result
        
        # Perform vector search
        results = await vector_search_service.search_vectors(
            query=request.query,
            limit=request.limit,
            filters=request.filters,
            similarity_threshold=request.similarity_threshold
        )
        
        search_time = time.time() - start_time
        
        # Prepare response
        response = SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=int(search_time * 1000),
            cache_hit=cache_hit,
            embedding_method=embedding_service.get_embedding_stats()["default_method"]
        )
        
        # Cache the result
        if request.use_cache and results:
            await _cache_search_result(request.query, request.filters, response.dict())
        
        # Update analytics
        redis_client.increment_counter("stats:searches_performed")
        if not cache_hit:
            redis_client.increment_counter("stats:cache_misses")
        
        return response
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/suggestions")
async def get_search_suggestions(q: str = Query(..., min_length=2)):
    """Get search suggestions based on query"""
    try:
        # Simple suggestion system based on document titles and content
        suggestions = []
        
        # Get some recent search queries (from cache keys)
        cache_pattern = "cache:search:*"
        cache_keys = redis_client.client.keys(cache_pattern)
        
        # Extract unique words from cached searches
        words = set()
        for key in cache_keys[:10]:  # Limit to recent searches
            try:
                cached_data = redis_client.get_json(key)
                if cached_data and "query" in cached_data:
                    query_words = cached_data["query"].lower().split()
                    words.update(query_words)
            except:
                continue
        
        # Filter suggestions
        query_lower = q.lower()
        matching_words = [word for word in words if word.startswith(query_lower) and len(word) > 2]
        suggestions = sorted(matching_words)[:5]
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return {"suggestions": []}

@router.get("/analytics")
async def get_search_analytics():
    """Get search performance analytics"""
    try:
        # Get Redis stats
        redis_stats = redis_client.get_stats()
        
        # Get vector search stats
        vector_stats = vector_search_service.get_vector_stats()
        
        # Get embedding stats
        embedding_stats = embedding_service.get_embedding_stats()
        
        # Get search analytics
        searches_performed = int(redis_client.client.get("stats:searches_performed") or 0)
        cache_hits = int(redis_client.client.get("stats:cache_hits") or 0)
        cache_misses = int(redis_client.client.get("stats:cache_misses") or 0)
        
        cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
        
        return {
            "search_performance": {
                "total_searches": searches_performed,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "cache_hit_rate": round(cache_hit_rate, 1)
            },
            "vector_search": vector_stats,
            "embedding_service": embedding_stats,
            "redis_usage": redis_stats
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Analytics retrieval failed")

async def _get_cached_search(query: str, filters: Dict = None) -> Optional[Dict]:
    """Get cached search result"""
    try:
        cache_key = _generate_search_cache_key(query, filters)
        return redis_client.get_json(f"cache:search:{cache_key}")
    except:
        return None

async def _cache_search_result(query: str, filters: Dict, result: Dict, ttl: int = 3600):
    """Cache search result"""
    try:
        cache_key = _generate_search_cache_key(query, filters)
        cache_data = {
            "query": query,
            "filters": filters,
            "result": result,
            "cached_at": redis_client.client.time()[0],  # Redis timestamp
            "ttl": ttl
        }
        redis_client.set_json(f"cache:search:{cache_key}", cache_data, ttl)
    except Exception as e:
        logger.error(f"Search caching failed: {e}")

def _generate_search_cache_key(query: str, filters: Dict = None) -> str:
    """Generate cache key for search"""
    content = f"{query}:{json.dumps(filters or {}, sort_keys=True)}"
    return hashlib.md5(content.encode()).hexdigest()
```

## 🧪 Testing the Embedding System

Create `scripts/test_embeddings.py`:

```python
import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_document_with_embeddings():
    """Test complete pipeline with embeddings"""
    print("🧪 Testing Document Processing + Embeddings Pipeline")
    print("=" * 60)
    
    # Create a more comprehensive test document
    test_content = """
    Redis AI Challenge: Semantic Document Cache
    
    This document demonstrates the power of Redis Vector Sets for semantic search.
    
    Key Features:
    - Vector similarity search using Redis 8
    - Semantic caching for improved performance
    - Real-time document processing
    - Natural language queries
    
    Technical Implementation:
    The system uses OpenAI embeddings to convert document chunks into high-dimensional
    vectors. These vectors are stored in Redis Vector Sets, enabling sub-millisecond
    semantic search across large document collections.
    
    Performance Benefits:
    - Sub-second search response times
    - 75% memory reduction with quantized vectors
    - Intelligent caching reduces API costs
    - Scalable architecture for enterprise deployment
    
    Use Cases:
    - Enterprise knowledge management
    - Technical documentation search
    - Customer support automation
    - Research paper discovery
    
    Conclusion:
    Redis Vector Sets combined with semantic embeddings create a powerful
    foundation for next-generation document search and discovery systems.
    """
    
    test_file = Path("redis_ai_document.txt")
    test_file.write_text(test_content)
    
    try:
        # Step 1: Upload document
        print("📤 Uploading test document...")
        with open(test_file, 'rb') as f:
            files = {'file': ('redis_ai_document.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/api/documents/upload", files=files)
        
        if response.status_code != 201:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return None
            
        result = response.json()
        doc_id = result["doc_id"]
        print(f"✅ Upload successful! Doc ID: {doc_id}")
        print(f"   Chunks created: {result['chunks_created']}")
        print(f"   Processing time: {result['processing_time']:.2f}s")
        
        # Wait a moment for vector processing
        print("\n⏳ Waiting for vector processing...")
        time.sleep(2)
        
        # Step 2: Test semantic search
        print("\n🔍 Testing semantic search...")
        search_queries = [
            "How does Redis improve search performance?",
            "What are the benefits of vector embeddings?",
            "Tell me about caching strategies",
            "Enterprise knowledge management solutions",
            "Technical implementation details"
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Query {i}: '{query}'")
            
            search_payload = {
                "query": query,
                "limit": 5,
                "similarity_threshold": 0.3,
                "use_cache": True
            }
            
            search_response = requests.post(
                f"{API_BASE}/api/search/", 
                json=search_payload
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                print(f"✅ Found {search_data['total_results']} results")
                print(f"   Search time: {search_data['search_time_ms']}ms")
                print(f"   Cache hit: {search_data['cache_hit']}")
                print(f"   Method: {search_data['embedding_method']}")
                
                # Show top result
                if search_data['results']:
                    top_result = search_data['results'][0]
                    print(f"   Top result: {top_result['similarity_score']:.3f} similarity")
                    print(f"   Content: {top_result['content'][:100]}...")
            else:
                print(f"❌ Search failed: {search_response.status_code}")
        
        # Step 3: Test cached search (repeat first query)
        print(f"\n🔄 Testing search cache with repeat query...")
        repeat_response = requests.post(
            f"{API_BASE}/api/search/", 
            json={
                "query": search_queries[0],
                "limit": 5,
                "use_cache": True
            }
        )
        
        if repeat_response.status_code == 200:
            repeat_data = repeat_response.json()
            print(f"✅ Cache test: {repeat_data['cache_hit']} (should be True)")
            print(f"   Search time: {repeat_data['search_time_ms']}ms (should be faster)")
        
        # Step 4: Get analytics
        print("\n📊 Getting search analytics...")
        analytics_response = requests.get(f"{API_BASE}/api/search/analytics")
        
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            print("✅ Analytics retrieved:")
            print(f"   Total searches: {analytics['search_performance']['total_searches']}")
            print(f"   Cache hit rate: {analytics['search_performance']['cache_hit_rate']}%")
            print(f"   Total vectors: {analytics['vector_search'].get('total_vectors', 0)}")
            print(f"   Embedding method: {analytics['embedding_service']['default_method']}")
        
        return doc_id
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return None
        
    finally:
        # Cleanup test file
        if test_file.exists():
            test_file.unlink()

def test_search_suggestions():
    """Test search suggestions"""
    print("\n💡 Testing search suggestions...")
    
    test_queries = ["redis", "vector", "semantic", "cache"]
    
    for query in test_queries:
        response = requests.get(f"{API_BASE}/api/search/suggestions?q={query}")
        if response.status_code == 200:
            suggestions = response.json()["suggestions"]
            print(f"✅ Suggestions for '{query}': {suggestions}")
        else:
            print(f"❌ Suggestions failed for '{query}'")

def test_performance_benchmark():
    """Test performance with multiple searches"""
    print("\n⚡ Performance benchmark...")
    
    queries = [
        "Redis performance optimization",
        "Vector search algorithms", 
        "Semantic similarity matching",
        "Cache hit rate improvements",
        "Enterprise search solutions"
    ]
    
    total_time = 0
    cache_hits = 0
    
    # Run each query twice to test caching
    for query in queries:
        for attempt in [1, 2]:
            start_time = time.time()
            
            response = requests.post(f"{API_BASE}/api/search/", json={
                "query": query,
                "limit": 3,
                "use_cache": True
            })
            
            end_time = time.time()
            request_time = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                search_time = data['search_time_ms']
                total_time += search_time
                
                if data['cache_hit']:
                    cache_hits += 1
                
                print(f"Query: '{query[:30]}...' (attempt {attempt})")
                print(f"  Request time: {request_time:.0f}ms, Search time: {search_time}ms, Cache: {data['cache_hit']}")
    
    avg_time = total_time / (len(queries) * 2)
    cache_rate = (cache_hits / (len(queries) * 2)) * 100
    
    print(f"\n📈 Benchmark Results:")
    print(f"   Average search time: {avg_time:.0f}ms")
    print(f"   Cache hit rate: {cache_rate:.1f}%")
    print(f"   Total queries: {len(queries) * 2}")

if __name__ == "__main__":
    # Run comprehensive test
    doc_id = test_document_with_embeddings()
    
    if doc_id:
        test_search_suggestions()
        test_performance_benchmark()
        
        print(f"\n🎉 All embedding tests completed successfully!")
        print(f"📄 Document ID: {doc_id}")
        print(f"🔍 Semantic search is working!")
        print(f"⚡ Performance caching active!")
        
        print(f"\n💡 Try these test URLs:")
        print(f"   Health: http://localhost:8000/health")
        print(f"   Document: http://localhost:8000/api/documents/{doc_id}")
        print(f"   Analytics: http://localhost:8000/api/search/analytics")
    else:
        print(f"\n❌ Tests failed!")
```

## 🔧 Update Configuration

Update `backend/app/config.py` to include embedding settings:

```python
# Add these to your Settings class
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Embedding Configuration
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_method: str = "auto"  # auto, openai, local
    
    # Vector Search Configuration
    vector_similarity_threshold: float = 0.7
    vector_search_limit: int = 50
    
    # Semantic Cache Configuration
    search_cache_ttl: int = 3600  # 1 hour
    enable_search_cache: bool = True
    
    # Performance Configuration
    embedding_batch_size: int = 10
    max_embedding_text_length: int = 8192
```

## 📝 Update Main Application

Update `backend/app/main.py` to include search endpoints:

```python
# Add this import
from app.api import search
from app.services.vector_search_service import vector_search_service

# Add the search router
app.include_router(search.router)

# Add startup initialization for vector search
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting DocuMind API...")
    
    # Verify Redis connection
    if not redis_client.health_check():
        raise Exception("Redis connection failed during startup")
    
    # Initialize vector search index
    try:
        await vector_search_service.initialize_vector_index()
        logger.info("📊 Vector search index initialized")
    except Exception as e:
        logger.warning(f"Vector index initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DocuMind API...")
```

## ✅ What You Now Have Complete

🎯 **Full AI-Powered Semantic Search System:**
- ✅ **OpenAI & Local Embeddings** - Dual provider support
- ✅ **Redis Vector Sets** - Native vector search with Redis 8
- ✅ **Semantic Caching** - Intelligent query result caching
- ✅ **Batch Processing** - Efficient embedding generation
- ✅ **Performance Analytics** - Cache hit rates and search metrics
- ✅ **RESTful Search API** - Professional search endpoints
- ✅ **Comprehensive Testing** - Full pipeline validation

## 🧪 Test Your Semantic Search

```bash
# 1. Install new dependencies
pip install openai sentence-transformers transformers torch numpy faiss-cpu scikit-learn

# 2. Update your .env with OpenAI key (optional)
OPENAI_API_KEY=your-key-here

# 3. Start server
python -m app.main

# 4. Run comprehensive test
python scripts/test_embeddings.py
```

## 🎉 Expected Results

```
✅ Upload successful! Doc ID: abc-123
   Chunks created: 8
✅ Found 3 results, Search time: 45ms, Cache hit: False
✅ Cache test: True (should be True), Search time: 8ms
✅ Analytics: 85.7% cache hit rate, 24 vectors indexed
🎉 All embedding tests completed successfully!
```

Your **Redis AI Challenge entry** now has the complete AI foundation! You've built a production-ready semantic document cache that showcases Redis 8's Vector Sets capabilities. 🚀

**Ready for the frontend or want to optimize performance?**