"""
Document management API endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Optional
import logging
import hashlib
import uuid
from datetime import datetime

from app.database.models import (
    DocumentMetadata, DocumentContent, UploadResponse, 
    DocumentStatus, DocumentType, ErrorResponse
)
from app.database.redis_client import redis_client
from app.services.document_processor import DocumentProcessor
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize document processor
doc_processor = DocumentProcessor()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'txt']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Max size: {settings.max_file_size} bytes"
            )
        
        # Generate document ID and hash
        document_id = str(uuid.uuid4())
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Create document metadata
        metadata = DocumentMetadata(
            id=document_id,
            filename=file.filename,
            file_type=DocumentType(file_extension),
            file_size=len(content),
            content_hash=content_hash,
            processing_status=DocumentStatus.PENDING
        )
        
        # Store metadata in Redis
        redis_client.set_json(
            f"doc:meta:{document_id}", 
            metadata.dict(),
            ttl=None  # Persistent storage
        )
        
        # Process document asynchronously (in a real implementation, use background tasks)
        try:
            # Extract text content
            text_content = await doc_processor.extract_text(content, file_extension)
            
            # Create document content
            doc_content = DocumentContent(
                document_id=document_id,
                raw_text=text_content,
                processed_timestamp=datetime.utcnow()
            )
            
            # Store content in Redis
            redis_client.set_json(
                f"doc:content:{document_id}",
                doc_content.dict()
            )
            
            # Update status to completed
            metadata.processing_status = DocumentStatus.COMPLETED
            metadata.word_count = len(text_content.split())
            
            redis_client.set_json(
                f"doc:meta:{document_id}",
                metadata.dict()
            )
            
            # Increment document counter
            redis_client.increment_counter("stats:total_documents")
            
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            # Update status to failed
            metadata.processing_status = DocumentStatus.FAILED
            redis_client.set_json(
                f"doc:meta:{document_id}",
                metadata.dict()
            )
            logger.error(f"Document processing failed: {e}")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=len(content),
            status=metadata.processing_status,
            message="Document uploaded and processing initiated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
    """
    Get document metadata by ID
    """
    try:
        metadata = redis_client.get_json(f"doc:meta:{document_id}")
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentMetadata(**metadata)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{document_id}/content")
async def get_document_content(document_id: str):
    """
    Get document content by ID
    """
    try:
        content = redis_client.get_json(f"doc:content:{document_id}")
        if not content:
            raise HTTPException(status_code=404, detail="Document content not found")
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document content {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its content
    """
    try:
        # Check if document exists
        metadata = redis_client.get_json(f"doc:meta:{document_id}")
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete metadata and content
        redis_client.client.delete(f"doc:meta:{document_id}")
        redis_client.client.delete(f"doc:content:{document_id}")
        
        # Decrement document counter
        redis_client.client.decr("stats:total_documents")
        
        logger.info(f"Document {document_id} deleted successfully")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=List[DocumentMetadata])
async def list_documents(
    limit: int = 10,
    offset: int = 0,
    status: Optional[DocumentStatus] = None
):
    """
    List documents with pagination and filtering
    """
    try:
        # Get all document metadata keys
        keys = redis_client.client.keys("doc:meta:*")
        
        documents = []
        for key in keys[offset:offset + limit]:
            metadata = redis_client.get_json(key)
            if metadata:
                doc_meta = DocumentMetadata(**metadata)
                if status is None or doc_meta.processing_status == status:
                    documents.append(doc_meta)
        
        return documents
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
