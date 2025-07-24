"""
Data models for DocuMind application
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class DocumentMetadata(BaseModel):
    """Document metadata model"""
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_type: DocumentType = Field(..., description="Document type")
    file_size: int = Field(..., description="File size in bytes")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    content_hash: Optional[str] = Field(None, description="SHA256 hash of content")
    page_count: Optional[int] = Field(None, description="Number of pages/sections")
    word_count: Optional[int] = Field(None, description="Word count")
    language: Optional[str] = Field(None, description="Detected language")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    
class DocumentContent(BaseModel):
    """Document content model"""
    document_id: str = Field(..., description="Reference to document")
    raw_text: str = Field(..., description="Extracted text content")
    chunks: List[str] = Field(default_factory=list, description="Text chunks for processing")
    embeddings: Optional[List[List[float]]] = Field(None, description="Vector embeddings")
    processed_timestamp: Optional[datetime] = Field(None)

class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    include_metadata: bool = Field(default=True, description="Include document metadata")

class SearchResult(BaseModel):
    """Search result model"""
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Document filename")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    matched_chunk: str = Field(..., description="Matching text chunk")
    chunk_index: int = Field(..., description="Index of matching chunk")
    metadata: Optional[DocumentMetadata] = Field(None, description="Document metadata")
    highlight: Optional[str] = Field(None, description="Highlighted matching text")

class SearchResponse(BaseModel):
    """Search response model"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    processing_time: float = Field(..., description="Query processing time in seconds")
    cached: bool = Field(default=False, description="Whether results were cached")

class UploadResponse(BaseModel):
    """File upload response model"""
    document_id: str = Field(..., description="Generated document ID")
    filename: str = Field(..., description="Uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    status: DocumentStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")

class AnalyticsData(BaseModel):
    """Analytics data model"""
    total_documents: int = Field(..., description="Total documents in system")
    total_searches: int = Field(..., description="Total search queries")
    avg_response_time: float = Field(..., description="Average response time")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    storage_used: str = Field(..., description="Storage space used")
    popular_queries: List[str] = Field(..., description="Most popular search queries")
    document_types: Dict[str, int] = Field(..., description="Document type distribution")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
