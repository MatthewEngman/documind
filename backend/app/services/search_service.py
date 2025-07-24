"""
Search service for semantic document search
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from app.database.redis_client import redis_client
from app.services.embedding_service import EmbeddingService
from app.database.models import DocumentMetadata

logger = logging.getLogger(__name__)

class SearchService:
    """Service for performing semantic search on documents"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def search_similar_documents(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query embedding
        """
        try:
            # Get all document chunks with embeddings
            chunk_keys = redis_client.client.keys("doc:chunks:*")
            
            if not chunk_keys:
                logger.info("No document chunks found for search")
                return []
            
            similar_chunks = []
            
            for chunk_key in chunk_keys:
                try:
                    chunk_data = redis_client.get_json(chunk_key)
                    if not chunk_data or 'embedding' not in chunk_data:
                        continue
                    
                    # Calculate similarity
                    similarity = self.embedding_service.calculate_similarity(
                        query_embedding, 
                        chunk_data['embedding']
                    )
                    
                    if similarity >= threshold:
                        # Get document metadata
                        doc_id = chunk_data.get('document_id')
                        metadata = None
                        if doc_id:
                            metadata_raw = redis_client.get_json(f"doc:meta:{doc_id}")
                            if metadata_raw:
                                metadata = DocumentMetadata(**metadata_raw)
                        
                        # Apply filters if provided
                        if filters and not self._apply_filters(metadata, filters):
                            continue
                        
                        similar_chunks.append({
                            "document_id": doc_id,
                            "filename": metadata.filename if metadata else "unknown",
                            "similarity_score": similarity,
                            "matched_chunk": chunk_data.get('text', ''),
                            "chunk_index": chunk_data.get('chunk_index', 0),
                            "metadata": metadata,
                            "highlight": self._generate_highlight(
                                chunk_data.get('text', ''), 
                                similarity
                            )
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing chunk {chunk_key}: {e}")
                    continue
            
            # Sort by similarity score (descending) and limit results
            similar_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_chunks[:limit]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _apply_filters(self, metadata: Optional[DocumentMetadata], filters: Dict[str, Any]) -> bool:
        """
        Apply filters to search results
        """
        try:
            if not metadata or not filters:
                return True
            
            # File type filter
            if 'file_type' in filters:
                if metadata.file_type != filters['file_type']:
                    return False
            
            # Date range filter
            if 'date_from' in filters:
                date_from = datetime.fromisoformat(filters['date_from'])
                if metadata.upload_timestamp < date_from:
                    return False
            
            if 'date_to' in filters:
                date_to = datetime.fromisoformat(filters['date_to'])
                if metadata.upload_timestamp > date_to:
                    return False
            
            # File size filter
            if 'max_file_size' in filters:
                if metadata.file_size > filters['max_file_size']:
                    return False
            
            # Tags filter
            if 'tags' in filters:
                required_tags = set(filters['tags'])
                document_tags = set(metadata.tags)
                if not required_tags.issubset(document_tags):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Filter application failed: {e}")
            return True
    
    def _generate_highlight(self, text: str, similarity_score: float) -> str:
        """
        Generate highlighted text snippet (simple implementation)
        """
        try:
            if not text:
                return ""
            
            # For now, just return the first 200 characters
            # In production, implement proper text highlighting based on query terms
            max_length = 200
            if len(text) <= max_length:
                return text
            
            # Try to break at word boundary
            truncated = text[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # If we can break reasonably close to the end
                truncated = truncated[:last_space]
            
            return truncated + "..."
            
        except Exception as e:
            logger.warning(f"Highlight generation failed: {e}")
            return text[:200] if text else ""
    
    async def index_document_chunks(self, document_id: str, chunks: List[str]) -> bool:
        """
        Index document chunks with embeddings for search
        """
        try:
            if not chunks:
                logger.warning(f"No chunks to index for document {document_id}")
                return False
            
            # Generate embeddings for chunks
            embedded_chunks = await self.embedding_service.embed_document_chunks(chunks, document_id)
            
            if not embedded_chunks:
                logger.error(f"Failed to generate embeddings for document {document_id}")
                return False
            
            # Store chunks with embeddings in Redis
            for chunk_data in embedded_chunks:
                chunk_key = f"doc:chunks:{document_id}:{chunk_data['chunk_index']}"
                redis_client.set_json(chunk_key, chunk_data)
            
            logger.info(f"Indexed {len(embedded_chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Document indexing failed for {document_id}: {e}")
            return False
    
    async def remove_document_from_index(self, document_id: str) -> bool:
        """
        Remove document chunks from search index
        """
        try:
            # Find all chunk keys for this document
            chunk_keys = redis_client.client.keys(f"doc:chunks:{document_id}:*")
            
            if chunk_keys:
                redis_client.client.delete(*chunk_keys)
                logger.info(f"Removed {len(chunk_keys)} chunks from index for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove document {document_id} from index: {e}")
            return False
    
    async def reindex_document(self, document_id: str) -> bool:
        """
        Reindex a document (remove old chunks and create new ones)
        """
        try:
            # Get document content
            content_data = redis_client.get_json(f"doc:content:{document_id}")
            if not content_data:
                logger.error(f"No content found for document {document_id}")
                return False
            
            # Remove existing chunks
            await self.remove_document_from_index(document_id)
            
            # Re-chunk and index
            from app.services.document_processor import DocumentProcessor
            doc_processor = DocumentProcessor()
            
            chunks = doc_processor.chunk_text(content_data.get('raw_text', ''))
            success = await self.index_document_chunks(document_id, chunks)
            
            if success:
                logger.info(f"Successfully reindexed document {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Document reindexing failed for {document_id}: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search index
        """
        try:
            # Count total chunks
            chunk_keys = redis_client.client.keys("doc:chunks:*")
            total_chunks = len(chunk_keys)
            
            # Count unique documents
            document_ids = set()
            for key in chunk_keys:
                try:
                    chunk_data = redis_client.get_json(key)
                    if chunk_data and 'document_id' in chunk_data:
                        document_ids.add(chunk_data['document_id'])
                except:
                    continue
            
            # Get embedding model info
            model_info = self.embedding_service.get_model_info()
            
            return {
                "total_chunks": total_chunks,
                "indexed_documents": len(document_ids),
                "embedding_model": model_info["model_name"],
                "embedding_dimension": model_info["embedding_dimension"],
                "index_size_estimate": f"{total_chunks * model_info['embedding_dimension'] * 4 / 1024 / 1024:.2f} MB",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {
                "error": "Failed to get index statistics",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search (fallback for when embeddings are not available)
        """
        try:
            if not keywords:
                return []
            
            # Get all document content
            content_keys = redis_client.client.keys("doc:content:*")
            matching_docs = []
            
            for content_key in content_keys:
                try:
                    content_data = redis_client.get_json(content_key)
                    if not content_data or 'raw_text' not in content_data:
                        continue
                    
                    text = content_data['raw_text'].lower()
                    doc_id = content_data['document_id']
                    
                    # Count keyword matches
                    matches = sum(1 for keyword in keywords if keyword.lower() in text)
                    
                    if matches > 0:
                        # Get metadata
                        metadata_raw = redis_client.get_json(f"doc:meta:{doc_id}")
                        metadata = DocumentMetadata(**metadata_raw) if metadata_raw else None
                        
                        # Calculate simple relevance score
                        relevance = matches / len(keywords)
                        
                        matching_docs.append({
                            "document_id": doc_id,
                            "filename": metadata.filename if metadata else "unknown",
                            "similarity_score": relevance,
                            "matched_chunk": self._extract_keyword_context(text, keywords),
                            "chunk_index": 0,
                            "metadata": metadata,
                            "highlight": self._highlight_keywords(text[:200], keywords)
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing content key {content_key}: {e}")
                    continue
            
            # Sort by relevance and limit
            matching_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
            return matching_docs[:limit]
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def _extract_keyword_context(self, text: str, keywords: List[str], context_length: int = 200) -> str:
        """
        Extract context around keyword matches
        """
        try:
            for keyword in keywords:
                keyword_lower = keyword.lower()
                text_lower = text.lower()
                
                index = text_lower.find(keyword_lower)
                if index != -1:
                    start = max(0, index - context_length // 2)
                    end = min(len(text), index + len(keyword) + context_length // 2)
                    
                    context = text[start:end]
                    if start > 0:
                        context = "..." + context
                    if end < len(text):
                        context = context + "..."
                    
                    return context
            
            # If no keywords found, return beginning of text
            return text[:context_length] + ("..." if len(text) > context_length else "")
            
        except Exception as e:
            logger.warning(f"Context extraction failed: {e}")
            return text[:200]
    
    def _highlight_keywords(self, text: str, keywords: List[str]) -> str:
        """
        Simple keyword highlighting
        """
        try:
            highlighted = text
            for keyword in keywords:
                # Simple replacement (case-insensitive)
                import re
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                highlighted = pattern.sub(f"**{keyword}**", highlighted)
            
            return highlighted
            
        except Exception as e:
            logger.warning(f"Keyword highlighting failed: {e}")
            return text
