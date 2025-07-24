from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging

from app.services.document_processor import document_processor
from app.database.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a document"""
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Process document
        result = await document_processor.process_document(
            file_content, 
            file.filename
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "Document uploaded and processed successfully",
                "doc_id": result["doc_id"],
                "chunks_created": result["chunks_created"],
                "processing_time": result["processing_time"],
                "document": {
                    "id": result["document"]["id"],
                    "title": result["document"]["title"],
                    "filename": result["document"]["filename"],
                    "size_bytes": result["document"]["size_bytes"],
                    "word_count": result["document"]["word_count"],
                    "chunk_count": result["document"]["chunk_count"]
                }
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
async def list_documents(
    limit: int = 20,
    offset: int = 0
):
    """List all documents"""
    try:
        documents = await document_processor.list_documents(limit, offset)
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get document by ID"""
    try:
        document = await document_processor.get_document(doc_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks information
        chunks_key = f"doc:chunks:{doc_id}"
        chunks_data = redis_client.get_json(chunks_key)
        chunks_count = len(chunks_data.get("chunks", [])) if chunks_data else 0
        
        document["chunks_available"] = chunks_count
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete document"""
    try:
        success = await document_processor.delete_document(doc_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    limit: int = 10,
    offset: int = 0
):
    """Get document chunks"""
    try:
        # Verify document exists
        document = await document_processor.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        chunks_key = f"doc:chunks:{doc_id}"
        chunks_data = redis_client.get_json(chunks_key)
        
        if not chunks_data or "chunks" not in chunks_data:
            return {"chunks": [], "total": 0}
        
        chunk_ids = chunks_data["chunks"][offset:offset + limit]
        chunks = []
        
        for chunk_id in chunk_ids:
            chunk_key = f"doc:chunk:{chunk_id}"
            chunk_data = redis_client.get_json(chunk_key)
            if chunk_data:
                chunks.append(chunk_data)
        
        return {
            "chunks": chunks,
            "total": len(chunks_data["chunks"]),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chunks error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{doc_id}/status")
async def get_processing_status(doc_id: str):
    """Get document processing status"""
    try:
        status = document_processor.get_processing_status(doc_id)
        
        if not status:
            # Check if document exists (completed processing)
            document = await document_processor.get_document(doc_id)
            if document:
                return {
                    "status": "completed",
                    "progress": 100,
                    "message": "Document processing completed"
                }
            else:
                raise HTTPException(status_code=404, detail="Processing status not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
