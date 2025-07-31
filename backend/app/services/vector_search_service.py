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
            # Check if Redis Stack is available
            try:
                from redis.commands.search.field import VectorField, TextField, NumericField, TagField
                from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            except ImportError:
                logger.warning("Redis Stack modules not available, using fallback vector search")
                self.initialized = True
                return
            
            # Check if index already exists
            try:
                if redis_client.client:
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
            if redis_client.client:
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
            # Use fallback mode
            self.initialized = True
            logger.info("Using fallback vector search without Redis Stack")
    
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
                    # Debug: Log chunk structure
                    chunk_id = chunk.get('id', chunk.get('chunk_id', 'MISSING_CHUNK_ID'))
                    logger.info(f"Processing chunk with ID: {chunk_id}")
                    logger.info(f"Chunk keys: {list(chunk.keys())}")
                    
                    # Prepare vector data for Redis
                    vector_key = f"vector:{chunk_id}"
                    
                    # Serialize vector
                    vector_bytes = self._serialize_vector(embedding["vector"])
                    logger.info(f"Serialized vector: {len(vector_bytes)} bytes")
                    
                    # Prepare document data
                    vector_data = {
                        "vector": vector_bytes,
                        "content": chunk["text"][:1000],  # Truncate for storage efficiency
                        "title": chunk.get("title", ""),
                        "filename": chunk.get("filename", ""),
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "tags": "|".join(chunk.get("tags", [])),
                        "word_count": chunk["word_count"],
                        "chunk_index": chunk.get("chunk_index", 0),
                        "upload_date": chunk.get("created_at", datetime.utcnow().isoformat()),
                        "embedding_method": embedding["method"],
                        "embedding_model": embedding["model"]
                    }
                    
                    logger.info(f"Prepared vector data for chunk {chunk_id}")
                    
                    # Store in Redis
                    if redis_client.client:
                        redis_client.client.hset(vector_key, mapping=vector_data)
                        vectors_added += 1
                        logger.info(f"Successfully stored vector for chunk {chunk_id}")
                    
                except Exception as e:
                    chunk_id_safe = chunk.get('chunk_id', 'UNKNOWN') if isinstance(chunk, dict) else 'NOT_DICT'
                    logger.error(f"Failed to add vector for chunk {chunk_id_safe}: {e}")
                    logger.error(f"Chunk type: {type(chunk)}, Embedding type: {type(embedding)}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            
            logger.info(f"Added {vectors_added}/{len(chunks_data)} vectors for document {doc_id}")
            
            # Update analytics
            if redis_client.client:
                redis_client.client.incrby("stats:vectors_created", vectors_added)
            
            return vectors_added
            
        except Exception as e:
            logger.error(f"Failed to add document vectors: {e}")
            raise
    
    async def search_vectors(self, 
                           query: str, 
                           limit: int = 10,
                           filters: Optional[Dict] = None,
                           similarity_threshold: float = 0.7) -> List[Dict]:
        """Perform semantic vector search"""
        try:
            if not self.initialized:
                await self.initialize_vector_index()
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query)
            query_vector = query_embedding["vector"]
            
            # Try Redis Stack vector search first
            try:
                results = await self._execute_redis_vector_search(query_vector, filters, limit)
            except:
                # Fallback to manual vector search
                logger.info("Using fallback vector search")
                results = await self._execute_fallback_vector_search(query_vector, filters, limit)
            
            # Process and rank results
            processed_results = self._process_search_results(results, query_vector, similarity_threshold)
            
            logger.info(f"Vector search completed: {len(processed_results)} results for query: '{query[:50]}...'")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _execute_redis_stack_search(self, query_vector: np.ndarray, limit: int, filters: Dict = None):
        """Execute Redis Stack vector search with correct query syntax"""
        try:
            # Convert to bytes properly for Redis Stack
            query_blob = query_vector.tobytes()
            
            logger.info(f"Query vector serialized: {len(query_blob)} bytes, type: {type(query_blob)}")
            logger.info(f"Query blob hex (first 20 chars): {query_blob.hex()[:20]}...")
            logger.info(f"Executing Redis Stack search with {len(query_blob)} byte vector")
            
            # Try different Redis Stack query syntaxes
            query_syntaxes = [
                # Syntax 1: Standard KNN query
                f"*=>[KNN {limit} @vector $query_vector AS score]",
                
                # Syntax 2: Alternative format
                f"*=>[KNN {limit} @vector $query_vector]",
                
                # Syntax 3: Simplified format
                f"*=>[KNN {limit} @vector $blob AS distance]",
                
                # Syntax 4: With parentheses
                f"(*)=>[KNN {limit} @vector $query_vector AS score]",
                
                # Syntax 5: Different parameter name
                f"*=>[KNN {limit} @vector $vec AS score]"
            ]
            
            for i, vector_query in enumerate(query_syntaxes):
                try:
                    logger.info(f"Trying query syntax {i+1}: {vector_query}")
                    
                    # Execute search with proper query parameters
                    results = redis_client.client.ft(self.vector_index_name).search(
                        vector_query,
                        query_params={
                            "query_vector": query_blob, 
                            "blob": query_blob,
                            "vec": query_blob
                        }
                    )
                    
                    logger.info(f"✅ Query syntax {i+1} successful! Found {len(results.docs)} results")
                    
                    # Convert results to list of dicts
                    search_results = []
                    for doc in results.docs:
                        result = {
                            "id": doc.id,
                            "score": float(doc.score) if hasattr(doc, 'score') else 0.0
                        }
                        # Add all document fields
                        for key, value in doc.__dict__.items():
                            if not key.startswith('_'):
                                result[key] = value
                        
                        search_results.append(result)
                    
                    return search_results
                    
                except Exception as syntax_error:
                    logger.warning(f"Query syntax {i+1} failed: {syntax_error}")
                    continue
            
            # If all syntaxes fail, raise the last error
            raise Exception("All Redis Stack query syntaxes failed")
            
        except Exception as e:
            logger.error(f"Redis Stack vector search execution failed: {e}")
            raise
    
    async def _execute_fallback_search(self, query_vector: np.ndarray, limit: int, filters: Dict = None):
        """Enhanced fallback vector search with better error handling"""
        try:
            # Get all vector keys
            vector_keys = redis_client.client.keys("vector:*")
            
            if not vector_keys:
                logger.info("No vectors found for fallback search")
                return []
            
            results = []
            processed_count = 0
            
            for key in vector_keys:
                try:
                    # Limit processing for performance
                    if processed_count >= 100:
                        break
                    
                    # Get vector data
                    vector_data = redis_client.client.hgetall(key)
                    if not vector_data or "vector" not in vector_data:
                        continue
                    
                    # Deserialize stored vector
                    stored_vector_bytes = vector_data["vector"]
                    
                    # Handle different encoding formats
                    if isinstance(stored_vector_bytes, str):
                        try:
                            # Try base64 decode first
                            stored_vector_bytes = base64.b64decode(stored_vector_bytes)
                        except:
                            try:
                                # Try direct string to bytes
                                stored_vector_bytes = stored_vector_bytes.encode('latin-1')
                            except:
                                continue
                    
                    # Convert bytes to numpy array
                    if len(stored_vector_bytes) != len(query_vector) * 4:
                        logger.debug(f"Vector size mismatch for {key}: {len(stored_vector_bytes)} vs {len(query_vector) * 4}")
                        continue
                    
                    stored_vector = np.frombuffer(stored_vector_bytes, dtype=np.float32)
                    
                    # Calculate cosine similarity
                    similarity = self._calculate_cosine_similarity(query_vector, stored_vector)
                    
                    if similarity >= 0.1:  # Lower threshold for demo
                        result = {
                            "id": key,
                            "score": 1.0 - similarity,  # Convert similarity to distance
                            "similarity": similarity,
                            **{k: v for k, v in vector_data.items() if k != "vector"}
                        }
                        results.append(result)
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.debug(f"Error processing vector {key}: {e}")
                    continue
            
            logger.info(f"Processed {processed_count} vectors, found {len(results)} matches")
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Fallback vector search failed: {e}")
            return []
    
    def _process_search_results(self, results: List[Dict], query_vector: List[float], threshold: float) -> List[Dict]:
        """Process and enhance search results"""
        processed = []
        
        for result in results:
            try:
                # Calculate actual similarity if not already present
                if "similarity" not in result:
                    if "vector" in result:
                        doc_vector = self._deserialize_vector(result["vector"])
                        similarity = embedding_service.calculate_similarity(query_vector, doc_vector)
                    else:
                        similarity = 1.0 - float(result.get("score", 1.0))  # Convert distance to similarity
                else:
                    similarity = float(result["similarity"])
                
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
            # Get all vector keys for the document
            if not redis_client.client:
                return False
            all_keys = redis_client.client.keys("vector:*")
            deleted_count = 0
            
            for key in all_keys:
                try:
                    vector_data = redis_client.client.hget(key, "doc_id")
                    if vector_data:
                        stored_doc_id = vector_data.decode() if isinstance(vector_data, bytes) else vector_data
                        if stored_doc_id == doc_id:
                            redis_client.client.delete(key)
                            deleted_count += 1
                except Exception as e:
                    logger.debug(f"Error checking vector {key}: {e}")
                    continue
            
            logger.info(f"Deleted {deleted_count} vectors for document {doc_id}")
            
            # Update analytics
            if redis_client.client:
                redis_client.client.incrby("stats:vectors_deleted", deleted_count)
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            return False
    
    def _serialize_vector(self, vector: List[float]) -> bytes:
        """Serialize vector for Redis storage (per Python redis-py docs)"""
        import numpy as np
        # Ensure vector is exactly the right format for Redis Stack
        vector_array = np.array(vector, dtype=np.float32)
        
        # Validate dimensions
        if len(vector_array) != settings.embedding_dimensions:
            raise ValueError(f"Vector dimension mismatch: got {len(vector_array)}, expected {settings.embedding_dimensions}")
        
        # Convert to bytes in little-endian format (Redis Stack default)
        vector_bytes = vector_array.astype('<f4').tobytes()
        
        logger.info(f"Serialized vector: {len(vector)} floats -> {len(vector_bytes)} bytes")
        return vector_bytes
    
    def _deserialize_vector(self, vector_bytes: bytes) -> List[float]:
        """Deserialize vector from Redis (backward compatible)"""
        import numpy as np
        import struct
        
        try:
            # Try new numpy format first
            return np.frombuffer(vector_bytes, dtype=np.float32).tolist()
        except Exception:
            try:
                # Fallback to old struct format for backward compatibility
                num_floats = len(vector_bytes) // 4
                return list(struct.unpack(f'{num_floats}f', vector_bytes))
            except Exception as e:
                logger.error(f"Failed to deserialize vector: {e}")
                raise
    
    def get_vector_stats(self) -> Dict:
        """Get vector search statistics"""
        try:
            # Count vector keys
            if not redis_client.client:
                return {"status": "error", "error": "Redis client not available"}
            vector_keys = redis_client.client.keys("vector:*")
            total_vectors = len(vector_keys)
            
            return {
                "status": "initialized" if self.initialized else "not_initialized",
                "index_name": self.vector_index_name,
                "total_docs": total_vectors,
                "indexing": False,
                "total_vectors": redis_client.client.get("stats:vectors_created") or 0,
                "deleted_vectors": redis_client.client.get("stats:vectors_deleted") or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting vector stats: {e}")
            return {"status": "error", "error": str(e)}

# Global instance
vector_search_service = VectorSearchService()
