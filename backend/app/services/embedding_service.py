"""
Embedding service for generating vector embeddings
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import hashlib

from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing document embeddings"""
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.embedding_dim = settings.embedding_dimensions
        self._model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            # Try to use OpenAI embeddings if API key is available
            if settings.openai_api_key:
                self._init_openai_embeddings()
            else:
                # Fallback to sentence-transformers
                self._init_sentence_transformers()
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            # Use dummy embeddings as fallback
            self._model = "dummy"
            logger.warning("Using dummy embeddings - install proper embedding model for production")
    
    def _init_openai_embeddings(self):
        """Initialize OpenAI embeddings"""
        try:
            import openai
            openai.api_key = settings.openai_api_key
            self._model = "openai"
            logger.info("Initialized OpenAI embeddings")
        except ImportError:
            logger.warning("OpenAI package not installed, falling back to sentence-transformers")
            self._init_sentence_transformers()
    
    def _init_sentence_transformers(self):
        """Initialize sentence-transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            # Use a lightweight model for development
            model_name = "all-MiniLM-L6-v2"  # 384 dimensions, fast and efficient
            self._model = SentenceTransformer(model_name)
            self.embedding_dim = 384  # Update dimension for this model
            logger.info(f"Initialized sentence-transformers model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using dummy embeddings")
            self._model = "dummy"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        try:
            if not text or not text.strip():
                return [0.0] * self.embedding_dim
            
            if self._model == "openai":
                return await self._generate_openai_embedding(text)
            elif hasattr(self._model, 'encode'):
                return await self._generate_sentence_transformer_embedding(text)
            else:
                return self._generate_dummy_embedding(text)
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._generate_dummy_embedding(text)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        """
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                return [[0.0] * self.embedding_dim] * len(texts)
            
            if self._model == "openai":
                return await self._generate_openai_embeddings_batch(valid_texts)
            elif hasattr(self._model, 'encode'):
                return await self._generate_sentence_transformer_embeddings_batch(valid_texts)
            else:
                return [self._generate_dummy_embedding(text) for text in valid_texts]
                
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [self._generate_dummy_embedding(text) for text in texts]
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            import openai
            
            response = await openai.Embedding.acreate(
                model=self.model_name,
                input=text.replace("\n", " ")
            )
            
            return response['data'][0]['embedding']
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return self._generate_dummy_embedding(text)
    
    async def _generate_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API in batch"""
        try:
            import openai
            
            # Clean texts
            cleaned_texts = [text.replace("\n", " ") for text in texts]
            
            response = await openai.Embedding.acreate(
                model=self.model_name,
                input=cleaned_texts
            )
            
            return [item['embedding'] for item in response['data']]
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            return [self._generate_dummy_embedding(text) for text in texts]
    
    async def _generate_sentence_transformer_embedding(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers"""
        try:
            embedding = self._model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Sentence transformer embedding failed: {e}")
            return self._generate_dummy_embedding(text)
    
    async def _generate_sentence_transformer_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers in batch"""
        try:
            embeddings = self._model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Sentence transformer batch embedding failed: {e}")
            return [self._generate_dummy_embedding(text) for text in texts]
    
    def _generate_dummy_embedding(self, text: str) -> List[float]:
        """Generate a dummy embedding based on text hash (for development/testing)"""
        try:
            # Create a deterministic embedding based on text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Convert hash to numbers and normalize
            hash_numbers = [int(text_hash[i:i+2], 16) for i in range(0, min(len(text_hash), 32), 2)]
            
            # Pad or truncate to desired dimension
            if len(hash_numbers) < self.embedding_dim:
                hash_numbers.extend([0] * (self.embedding_dim - len(hash_numbers)))
            else:
                hash_numbers = hash_numbers[:self.embedding_dim]
            
            # Normalize to [-1, 1] range
            normalized = [(x - 127.5) / 127.5 for x in hash_numbers]
            
            return normalized
            
        except Exception as e:
            logger.error(f"Dummy embedding generation failed: {e}")
            return [0.0] * self.embedding_dim
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        try:
            if len(embedding1) != len(embedding2):
                logger.warning("Embedding dimensions don't match")
                return 0.0
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure similarity is in [0, 1] range
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current embedding model
        """
        return {
            "model_type": "openai" if self._model == "openai" else "sentence_transformer" if hasattr(self._model, 'encode') else "dummy",
            "model_name": self.model_name if self._model == "openai" else getattr(self._model, 'model_name', 'unknown') if hasattr(self._model, 'encode') else "dummy",
            "embedding_dimension": self.embedding_dim,
            "initialized": self._model is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def embed_document_chunks(self, chunks: List[str], document_id: str) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks and return structured data
        """
        try:
            if not chunks:
                return []
            
            # Generate embeddings for all chunks
            embeddings = await self.generate_embeddings_batch(chunks)
            
            # Structure the data
            embedded_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedded_chunks.append({
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk,
                    "embedding": embedding,
                    "embedding_model": self.get_model_info()["model_name"],
                    "created_at": datetime.utcnow().isoformat()
                })
            
            return embedded_chunks
            
        except Exception as e:
            logger.error(f"Document chunk embedding failed: {e}")
            return []

# Global instance
embedding_service = EmbeddingService()
