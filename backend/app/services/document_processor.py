import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from app.database.redis_client import redis_client
from app.services.file_handler import file_handler
from app.services.text_extractor import text_extractor
from app.services.text_chunker import text_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_search_service import vector_search_service

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main document processing pipeline orchestrator"""
    
    def __init__(self):
        self.processing_status = {}
    
    async def process_document(self, file_content: bytes, filename: str, doc_id: str = None) -> Dict:
        """Process uploaded document through the complete pipeline"""
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate file
            self._update_status(doc_id, "validating", 5)
            validation_result = await file_handler.validate_file(file_content, filename)
            
            if not validation_result["valid"]:
                raise ValueError(validation_result["error"])
            
            # Step 2: Save file
            self._update_status(doc_id, "saving", 10)
            file_metadata = await file_handler.save_file(file_content, filename)
            
            # Step 3: Extract text
            self._update_status(doc_id, "extracting", 25)
            extraction_result = await text_extractor.extract_text(
                file_content, filename, validation_result["mime_type"]
            )
            
            if not extraction_result["success"]:
                raise ValueError(f"Text extraction failed: {extraction_result['error']}")
            
            # Step 4: Generate chunks
            self._update_status(doc_id, "chunking", 50)
            chunks = await text_chunker.chunk_text(
                extraction_result["text"], 
                doc_id, 
                {"filename": filename}
            )
            
            if not chunks:
                raise ValueError("No valid chunks created from document")
            
            # Step 5: Generate and store vectors
            self._update_status(doc_id, "generating_vectors", 65)
            try:
                vectors_added = await vector_search_service.add_document_vectors(doc_id, chunks)
                logger.info(f"Generated {vectors_added} vectors for document {doc_id}")
            except Exception as e:
                logger.warning(f"Vector generation failed for {doc_id}: {e}")
                # Continue processing even if vector generation fails
            
            # Step 6: Store document metadata
            self._update_status(doc_id, "storing", 75)
            document = {
                "id": doc_id,
                "title": self._generate_title(filename, extraction_result["text"]),
                "filename": filename,
                "original_filename": filename,
                "file_path": file_metadata["file_path"],
                "file_hash": file_metadata["file_hash"],
                "mime_type": validation_result["mime_type"],
                "size_bytes": validation_result["size_bytes"],
                "word_count": extraction_result.get("word_count", 0),
                "char_count": extraction_result.get("char_count", 0),
                "page_count": extraction_result.get("page_count", 0),
                "chunk_count": len(chunks),
                "extractor_used": extraction_result.get("extractor", "unknown"),
                "tags": self._generate_tags(extraction_result, validation_result),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "processed"
            }
            
            # Store document in Redis
            redis_client.set_json(f"doc:{doc_id}", document)
            
            # Store chunks and create chunk index
            chunk_ids = []
            for chunk in chunks:
                redis_client.set_json(f"doc:chunk:{chunk['id']}", chunk)
                chunk_ids.append(chunk['id'])
            
            # Store chunk index for this document
            redis_client.set_json(f"doc:chunks:{doc_id}", {
                "doc_id": doc_id,
                "chunks": chunk_ids,
                "total_chunks": len(chunks),
                "created_at": datetime.utcnow().isoformat()
            })
            
            # Add to document index
            redis_client.client.sadd("doc:index", doc_id)
            
            # Update statistics
            redis_client.client.incr("stats:documents_processed")
            redis_client.client.incrby("stats:chunks_created", len(chunks))
            
            # Step 6: Generate and store vectors
            try:
                self._update_status(doc_id, "generating_vectors", 85)
                
                # Prepare chunks data for vector generation
                chunks_data = []
                for chunk in chunks:
                    chunk_data = {
                        "chunk_id": chunk["id"],
                        "doc_id": doc_id,
                        "text": chunk["text"],
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"],
                        "word_count": chunk["word_count"],
                        "chunk_index": chunk["chunk_index"],
                        "metadata": chunk["metadata"],
                        "title": document["title"],
                        "filename": document["filename"],
                        "tags": document.get("tags", []),
                        "upload_date": document["created_at"]
                    }
                    chunks_data.append(chunk_data)
                
                # Generate and store vectors
                vectors_added = await vector_search_service.add_document_vectors(doc_id, chunks_data)
                document["vectors_generated"] = vectors_added
                
                logger.info(f"Generated {vectors_added} vectors for document {doc_id}")
                
                # Update document with vector info
                redis_client.set_json(f"doc:{doc_id}", document)
                
            except Exception as e:
                logger.error(f"Vector generation failed for {doc_id}: {e}")
                document["vector_error"] = str(e)
                redis_client.set_json(f"doc:{doc_id}", document)
            
            # Step 7: Complete processing
            self._update_status(doc_id, "completed", 100)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Clean up status after delay
            self._cleanup_status(doc_id)
            
            logger.info(f"Document {doc_id} processed successfully: {len(chunks)} chunks in {processing_time:.2f}s")
            
            return {
                "doc_id": doc_id,
                "chunks_created": len(chunks),
                "processing_time": processing_time,
                "status": "success",
                "document": {
                    "id": document["id"],
                    "title": document["title"],
                    "filename": document["filename"],
                    "size_bytes": document["size_bytes"],
                    "word_count": document["word_count"],
                    "chunk_count": document["chunk_count"]
                }
            }
            
        except Exception as e:
            self._update_status(doc_id, "failed", 0, str(e))
            logger.error(f"Document processing failed for {filename}: {e}")
            
            # Clean up any partial data
            await self._cleanup_failed_processing(doc_id)
            raise
    
    def _generate_title(self, filename: str, text: str) -> str:
        """Generate a meaningful title for the document"""
        # Use filename without extension as base
        base_title = filename.rsplit('.', 1)[0]
        
        # Try to find a better title from the text content
        lines = text.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 100:
                # This might be a title
                if not line.lower().startswith(('the ', 'a ', 'an ')):
                    return line[:80]  # Limit title length
        
        return base_title
    
    def _generate_tags(self, extraction_result: Dict, validation_result: Dict) -> List[str]:
        """Generate tags for the document based on content and metadata"""
        tags = []
        
        # File type tags
        file_ext = validation_result.get("extension", "").lower()
        if file_ext:
            tags.append(f"type{file_ext}")
        
        # Size-based tags
        size_mb = validation_result.get("size_bytes", 0) / (1024 * 1024)
        if size_mb > 10:
            tags.append("large")
        elif size_mb < 1:
            tags.append("small")
        else:
            tags.append("medium")
        
        # Content tags (basic keyword detection)
        text = extraction_result.get("text", "").lower()
        keywords_map = {
            "api": ["api", "endpoint", "rest", "graphql", "webhook"],
            "security": ["security", "authentication", "authorization", "encryption", "ssl", "tls"],
            "documentation": ["documentation", "guide", "manual", "readme", "instructions"],
            "technical": ["technical", "engineering", "development", "code", "programming"],
            "business": ["business", "strategy", "market", "revenue", "customer"],
            "report": ["report", "analysis", "summary", "findings", "conclusion"],
            "policy": ["policy", "procedure", "guidelines", "compliance", "standards"],
            "contract": ["contract", "agreement", "terms", "conditions", "legal"]
        }
        
        for tag, keywords in keywords_map.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        # Page/length tags
        if "page_count" in extraction_result:
            page_count = extraction_result["page_count"]
            if page_count > 50:
                tags.append("lengthy")
            elif page_count < 5:
                tags.append("brief")
        
        # Word count tags
        word_count = extraction_result.get("word_count", 0)
        if word_count > 5000:
            tags.append("detailed")
        elif word_count < 500:
            tags.append("concise")
        
        # Date-based tags (current month/year)
        current_date = datetime.utcnow()
        tags.append(f"uploaded_{current_date.strftime('%Y_%m')}")
        
        # Remove duplicates and return
        return list(set(tags))
    
    def _update_status(self, doc_id: str, status: str, progress: int, error: str = None):
        """Update processing status"""
        self.processing_status[doc_id] = {
            "status": status,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        }
    
    def _get_processing_time(self, doc_id: str) -> float:
        """Calculate processing time"""
        if doc_id not in self.processing_status:
            return 0
        
        start_time = datetime.fromisoformat(self.processing_status[doc_id]["timestamp"])
        end_time = datetime.utcnow()
        return (end_time - start_time).total_seconds()
    
    def _cleanup_status(self, doc_id: str, delay_seconds: int = 300):
        """Clean up processing status after delay"""
        import threading
        
        def cleanup():
            import time
            time.sleep(delay_seconds)
            self.processing_status.pop(doc_id, None)
        
        thread = threading.Thread(target=cleanup)
        thread.daemon = True
        thread.start()
    
    async def _cleanup_failed_processing(self, doc_id: str):
        """Clean up any data from failed processing"""
        try:
            # Remove document if it exists
            redis_client.client.delete(f"doc:{doc_id}")
            
            # Remove from index
            redis_client.client.srem("doc:index", doc_id)
            
            # Remove chunks index
            redis_client.client.delete(f"doc:chunks:{doc_id}")
            
            # Note: Individual chunks would need to be tracked and cleaned up
            # This is a simplified cleanup
            
        except Exception as e:
            logger.error(f"Failed cleanup for {doc_id}: {e}")
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document and all associated data including vectors"""
        try:
            # Get document metadata first
            doc_key = f"doc:{doc_id}"
            document = redis_client.get_json(doc_key)
            
            if not document:
                logger.warning(f"Document {doc_id} not found for deletion")
                return False
            
            # Delete vectors FIRST
            try:
                await vector_search_service.delete_document_vectors(doc_id)
                logger.info(f"Deleted vectors for document {doc_id}")
            except Exception as e:
                logger.error(f"Failed to delete vectors for {doc_id}: {e}")
            
            # Delete file from storage
            if "file_path" in document:
                try:
                    await file_handler.delete_file(document["file_path"])
                    logger.info(f"Deleted file: {document['file_path']}")
                except Exception as e:
                    logger.error(f"Failed to delete file {document['file_path']}: {e}")
            
            # Get chunks to delete
            chunks_key = f"doc:chunks:{doc_id}"
            chunks_data = redis_client.get_json(chunks_key)
            
            if chunks_data and "chunks" in chunks_data:
                # Delete individual chunks
                for chunk_id in chunks_data["chunks"]:
                    redis_client.client.delete(f"doc:chunk:{chunk_id}")
                logger.info(f"Deleted {len(chunks_data['chunks'])} chunks for document {doc_id}")
            
            # Delete document metadata
            redis_client.client.delete(doc_key)
            
            # Delete chunks index
            redis_client.client.delete(chunks_key)
            
            # Remove from document index
            redis_client.client.srem("doc:index", doc_id)
            
            # Update analytics
            redis_client.client.incr("stats:documents_deleted")
            
            logger.info(f"Document {doc_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def get_processing_status(self, doc_id: str) -> Optional[Dict]:
        """Get processing status for a document"""
        return self.processing_status.get(doc_id)
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        return redis_client.get_json(f"doc:{doc_id}")
    
    async def process_documents_batch(self, documents_data: List[Dict]) -> List[Dict]:
        """Process multiple documents concurrently with controlled concurrency"""
        MAX_CONCURRENT_DOCS = 3
        
        async def process_single_doc(doc_data):
            try:
                return await self.process_document(
                    doc_data["file_content"],
                    doc_data["filename"],
                    doc_data.get("doc_id")
                )
            except Exception as e:
                logger.error(f"Batch processing failed for {doc_data['filename']}: {e}")
                if doc_data.get("doc_id"):
                    self._update_status(doc_data["doc_id"], "failed", 0, str(e))
                raise
        
        results = []
        for i in range(0, len(documents_data), MAX_CONCURRENT_DOCS):
            batch = documents_data[i:i + MAX_CONCURRENT_DOCS]
            logger.info(f"Processing document batch {i//MAX_CONCURRENT_DOCS + 1}/{(len(documents_data)-1)//MAX_CONCURRENT_DOCS + 1}")
            
            batch_tasks = [process_single_doc(doc_data) for doc_data in batch]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Document processing failed: {result}")
                        results.append({"error": str(result), "filename": batch[j]["filename"]})
                    else:
                        results.append(result)
                
                if i + MAX_CONCURRENT_DOCS < len(documents_data):
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                raise
        
        return results

    async def list_documents(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """List all documents with pagination"""
        try:
            doc_ids = list(redis_client.client.smembers("doc:index"))
            doc_ids = [doc_id.decode() if isinstance(doc_id, bytes) else doc_id for doc_id in doc_ids]
            
            # Sort by creation date (newest first)
            documents_with_dates = []
            for doc_id in doc_ids:
                doc = redis_client.get_json(f"doc:{doc_id}")
                if doc:
                    documents_with_dates.append((doc, doc.get("created_at", "")))
            
            # Sort by date descending
            documents_with_dates.sort(key=lambda x: x[1], reverse=True)
            
            # Apply pagination
            paginated_docs = documents_with_dates[offset:offset + limit]
            
            return [doc[0] for doc in paginated_docs]
            
        except Exception as e:
            logger.error(f"List documents error: {e}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document and all associated data"""
        try:
            # Get document to check if it exists
            doc = redis_client.get_json(f"doc:{doc_id}")
            if not doc:
                return False
            
            # Get chunks to delete
            chunks_data = redis_client.get_json(f"doc:chunks:{doc_id}")
            if chunks_data and "chunks" in chunks_data:
                # Delete individual chunks
                for chunk_id in chunks_data["chunks"]:
                    redis_client.client.delete(f"doc:chunk:{chunk_id}")
            
            # Delete chunks index
            redis_client.client.delete(f"doc:chunks:{doc_id}")
            
            # Delete document
            redis_client.client.delete(f"doc:{doc_id}")
            
            # Remove from index
            redis_client.client.srem("doc:index", doc_id)
            
            # Delete file if it exists
            if "file_path" in doc:
                await file_handler.delete_file(doc["file_path"])
            
            # Update statistics
            redis_client.client.decr("stats:documents_processed")
            if chunks_data:
                chunk_count = len(chunks_data.get("chunks", []))
                redis_client.client.decrby("stats:chunks_created", chunk_count)
            
            logger.info(f"Document {doc_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Document deletion failed for {doc_id}: {e}")
            return False

# Global instance
document_processor = DocumentProcessor()
