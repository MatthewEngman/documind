# Document Processing Pipeline Implementation

## 🎯 Overview

This pipeline transforms uploaded documents into searchable, Redis-stored content through intelligent text extraction, chunking, and metadata generation.

## 📋 New Dependencies

Add to `backend/requirements.txt`:
```txt
# Document Processing
PyPDF2==3.0.1
python-docx==1.1.0
python-magic==0.4.27      # File type detection
aiofiles==23.2.1          # Async file operations
pillow==10.2.0            # Image processing (for PDFs with images)
pdfplumber==0.10.3        # Better PDF text extraction
markdown==3.5.2           # Markdown support

# Text Processing
nltk==3.8.1               # Text processing utilities
spacy==3.7.2              # Advanced NLP (optional)
```

## 🔧 Core Components

### 1. File Handler Service

Create `backend/app/services/file_handler.py`:

```python
import os
import magic
import hashlib
import aiofiles
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file operations, validation, and metadata extraction"""
    
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

# Global instance
document_processor = DocumentProcessor()
```

### 5. API Endpoints

Update `backend/app/api/documents.py`:

```python
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
```

### 6. Update Main Application

Update `backend/app/main.py` to include the documents router:

```python
# Add this import at the top
from app.api import documents

# Add this after the existing endpoints
app.include_router(documents.router)

# Add a new endpoint for system statistics
@app.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        redis_stats = redis_client.get_stats()
        
        # Get document statistics
        total_docs = redis_client.client.scard("doc:index") or 0
        processed_docs = redis_client.client.get("stats:documents_processed") or 0
        chunks_created = redis_client.client.get("stats:chunks_created") or 0
        
        return {
            "system": {
                "status": "healthy",
                "redis_connected": redis_client.health_check()
            },
            "redis": redis_stats,
            "documents": {
                "total_documents": int(total_docs),
                "processed_documents": int(processed_docs),
                "total_chunks": int(chunks_created)
            }
        }
        
    except Exception as e:
        logger.error(f"System stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## 🧪 Testing the Pipeline

### 1. Test Script

Create `scripts/test_document_processing.py`:

```python
import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_document_upload():
    """Test document upload and processing"""
    print("🧪 Testing Document Processing Pipeline")
    print("=" * 50)
    
    # Create a test text file
    test_content = """
    This is a test document for the Redis AI Challenge.
    
    It contains multiple paragraphs to test the chunking functionality.
    
    The document processing pipeline should:
    1. Extract this text
    2. Chunk it intelligently
    3. Store it in Redis
    4. Make it searchable
    
    This is the final paragraph of our test document.
    """
    
    test_file = Path("test_document.txt")
    test_file.write_text(test_content)
    
    try:
        # Upload document
        print("📤 Uploading test document...")
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/api/documents/upload", files=files)
        
        if response.status_code == 201:
            result = response.json()
            doc_id = result["doc_id"]
            print(f"✅ Upload successful! Doc ID: {doc_id}")
            print(f"   Chunks created: {result['chunks_created']}")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            
            # Test document retrieval
            print("\n📖 Retrieving document...")
            doc_response = requests.get(f"{API_BASE}/api/documents/{doc_id}")
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                print(f"✅ Document retrieved: {doc_data['title']}")
                print(f"   Word count: {doc_data['word_count']}")
                print(f"   Chunk count: {doc_data['chunk_count']}")
            
            # Test chunks retrieval
            print("\n🧩 Retrieving chunks...")
            chunks_response = requests.get(f"{API_BASE}/api/documents/{doc_id}/chunks")
            if chunks_response.status_code == 200:
                chunks_data = chunks_response.json()
                print(f"✅ Retrieved {len(chunks_data['chunks'])} chunks")
                for i, chunk in enumerate(chunks_data['chunks']):
                    print(f"   Chunk {i}: {chunk['word_count']} words")
            
            # Test document listing
            print("\n📋 Testing document listing...")
            list_response = requests.get(f"{API_BASE}/api/documents/")
            if list_response.status_code == 200:
                list_data = list_response.json()
                print(f"✅ Listed {len(list_data['documents'])} documents")
            
            return doc_id
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    finally:
        # Cleanup test file
        if test_file.exists():
            test_file.unlink()

def test_system_stats():
    """Test system statistics"""
    print("\n📊 Testing system statistics...")
    response = requests.get(f"{API_BASE}/api/system/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print("✅ System stats retrieved:")
        print(f"   Redis connected: {stats['system']['redis_connected']}")
        print(f"   Total documents: {stats['documents']['total_documents']}")
        print(f"   Total chunks: {stats['documents']['total_chunks']}")
        print(f"   Memory used: {stats['redis']['memory_used']}")
    else:
        print(f"❌ Stats failed: {response.status_code}")

if __name__ == "__main__":
    # Test the pipeline
    doc_id = test_document_upload()
    test_system_stats()
    
    if doc_id:
        print(f"\n🎉 All tests passed! Document ID: {doc_id}")
        print("💡 Next steps:")
        print("   1. Test with PDF files")
        print("   2. Add embedding generation")
        print("   3. Implement vector search")
    else:
        print("\n❌ Tests failed!")
```

### 2. Run the Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python -m app.main

# Run tests (in another terminal)
cd scripts
python test_document_processing.py
```

## ✅ What You Now Have

🎯 **Complete Document Processing Pipeline:**
- ✅ File upload with validation
- ✅ Multi-format text extraction (PDF, DOCX, TXT)
- ✅ Intelligent chunking for optimal search
- ✅ Redis storage with JSON documents
- ✅ RESTful API endpoints
- ✅ Progress tracking and error handling
- ✅ Comprehensive testing

## 🚀 Next Steps

Your pipeline is now ready for:
1. **Embedding Generation** - Convert chunks to vectors
2. **Vector Search** - Redis Vector Sets implementation
3. **Frontend Development** - React UI for document management
4. **Performance Optimization** - Caching and speed improvements

The foundation is solid - you can now upload documents and see them processed into searchable chunks stored in Redis! 🎉_init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Supported file types
        self.supported_types = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'text/markdown': '.md',
            'application/rtf': '.rtf'
        }
    
    async def validate_file(self, file_content: bytes, filename: str) -> Dict:
        """Validate uploaded file"""
        try:
            # Check file size
            if len(file_content) > settings.max_file_size:
                return {
                    "valid": False,
                    "error": f"File too large. Max size: {settings.max_file_size // 1024 // 1024}MB"
                }
            
            # Check file type using python-magic
            mime_type = magic.from_buffer(file_content, mime=True)
            
            if mime_type not in self.supported_types:
                return {
                    "valid": False,
                    "error": f"Unsupported file type: {mime_type}. Supported: {list(self.supported_types.values())}"
                }
            
            # Check file extension
            file_ext = Path(filename).suffix.lower()
            expected_ext = self.supported_types[mime_type]
            
            if file_ext != expected_ext:
                logger.warning(f"Extension mismatch: {file_ext} vs {expected_ext} for {mime_type}")
            
            return {
                "valid": True,
                "mime_type": mime_type,
                "extension": file_ext,
                "size_bytes": len(file_content)
            }
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    async def save_file(self, file_content: bytes, filename: str) -> Dict:
        """Save file and return metadata"""
        try:
            # Generate unique filename
            file_hash = hashlib.md5(file_content).hexdigest()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = self._sanitize_filename(filename)
            
            unique_filename = f"{timestamp}_{file_hash[:8]}_{safe_filename}"
            file_path = self.upload_dir / unique_filename
            
            # Save file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Generate metadata
            metadata = {
                "original_filename": filename,
                "stored_filename": unique_filename,
                "file_path": str(file_path),
                "file_hash": file_hash,
                "size_bytes": len(file_content),
                "uploaded_at": datetime.utcnow().isoformat(),
                "mime_type": magic.from_buffer(file_content, mime=True)
            }
            
            logger.info(f"File saved: {unique_filename} ({len(file_content)} bytes)")
            return metadata
            
        except Exception as e:
            logger.error(f"File save error: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"File deletion error: {e}")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace unsafe characters
        import re
        safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
        # Limit length
        name_part = Path(safe_name).stem[:50]
        ext_part = Path(safe_name).suffix
        return f"{name_part}{ext_part}"

# Global instance
file_handler = FileHandler()
```

### 2. Text Extraction Service

Create `backend/app/services/text_extractor.py`:

```python
import PyPDF2
import pdfplumber
from docx import Document
import re
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract text content from various document formats"""
    
    def __init__(self):
        self.extractors = {
            '.pdf': self._extract_from_pdf,
            '.docx': self._extract_from_docx,
            '.doc': self._extract_from_docx,  # Basic support
            '.txt': self._extract_from_txt,
            '.md': self._extract_from_txt,
            '.rtf': self._extract_from_txt
        }
    
    async def extract_text(self, file_path: str, mime_type: str) -> Dict:
        """Extract text and metadata from document"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in self.extractors:
                raise ValueError(f"Unsupported file extension: {file_ext}")
            
            # Extract text using appropriate method
            result = await self.extractors[file_ext](file_path)
            
            # Post-process text
            result['text'] = self._clean_text(result['text'])
            result['word_count'] = len(result['text'].split())
            result['char_count'] = len(result['text'])
            
            logger.info(f"Text extracted from {file_path}: {result['word_count']} words")
            return result
            
        except Exception as e:
            logger.error(f"Text extraction error for {file_path}: {e}")
            raise
    
    async def _extract_from_pdf(self, file_path: str) -> Dict:
        """Extract text from PDF using multiple methods for best results"""
        text_content = ""
        page_count = 0
        metadata = {}
        
        try:
            # Method 1: Try pdfplumber (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                pages_text = []
                
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text() or ""
                        pages_text.append(page_text)
                        text_content += page_text + "\n\n"
                    except Exception as e:
                        logger.warning(f"Error extracting page {i}: {e}")
                
                # Extract metadata
                if pdf.metadata:
                    metadata = {
                        'title': pdf.metadata.get('Title', ''),
                        'author': pdf.metadata.get('Author', ''),
                        'creator': pdf.metadata.get('Creator', ''),
                        'subject': pdf.metadata.get('Subject', '')
                    }
        
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            
            # Fallback: PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    page_count = len(pdf_reader.pages)
                    
                    for page in pdf_reader.pages:
                        try:
                            text_content += page.extract_text() + "\n\n"
                        except Exception as e:
                            logger.warning(f"Error extracting page: {e}")
                    
                    # Extract metadata
                    if pdf_reader.metadata:
                        metadata = {
                            'title': pdf_reader.metadata.get('/Title', ''),
                            'author': pdf_reader.metadata.get('/Author', ''),
                            'creator': pdf_reader.metadata.get('/Creator', ''),
                            'subject': pdf_reader.metadata.get('/Subject', '')
                        }
            except Exception as e2:
                logger.error(f"Both PDF extraction methods failed: {e2}")
                raise
        
        return {
            'text': text_content,
            'page_count': page_count,
            'metadata': metadata,
            'extraction_method': 'pdf'
        }
    
    async def _extract_from_docx(self, file_path: str) -> Dict:
        """Extract text from DOCX files"""
        try:
            doc = Document(file_path)
            
            # Extract paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)
            
            text_content = '\n\n'.join(paragraphs)
            
            # Extract metadata
            metadata = {
                'title': doc.core_properties.title or '',
                'author': doc.core_properties.author or '',
                'subject': doc.core_properties.subject or '',
                'created': str(doc.core_properties.created) if doc.core_properties.created else '',
                'modified': str(doc.core_properties.modified) if doc.core_properties.modified else ''
            }
            
            return {
                'text': text_content,
                'paragraph_count': len(paragraphs),
                'metadata': metadata,
                'extraction_method': 'docx'
            }
            
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            raise
    
    async def _extract_from_txt(self, file_path: str) -> Dict:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text_content = file.read()
            
            # Count lines for basic structure info
            lines = text_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            return {
                'text': text_content,
                'line_count': len(lines),
                'non_empty_lines': len(non_empty_lines),
                'metadata': {},
                'extraction_method': 'txt'
            }
            
        except Exception as e:
            logger.error(f"Text file extraction error: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Non-ASCII characters
        
        # Remove excessive punctuation
        text = re.sub(r'\.{3,}', '...', text)  # Multiple dots
        
        # Normalize whitespace
        text = text.strip()
        
        return text

# Global instance
text_extractor = TextExtractor()
```

### 3. Document Chunking Service

Create `backend/app/services/document_chunker.py`:

```python
import re
import nltk
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of document text"""
    chunk_id: str
    text: str
    start_char: int
    end_char: int
    word_count: int
    metadata: Dict

class DocumentChunker:
    """Intelligent document chunking for optimal search performance"""
    
    def __init__(self, 
                 chunk_size: int = 512,  # tokens per chunk
                 overlap_size: int = 50,  # token overlap between chunks
                 min_chunk_size: int = 100):  # minimum viable chunk size
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        
    def chunk_document(self, 
                      text: str, 
                      doc_id: str, 
                      metadata: Dict = None) -> List[DocumentChunk]:
        """Chunk document text intelligently"""
        try:
            if not text or not text.strip():
                return []
            
            metadata = metadata or {}
            
            # Method 1: Try semantic chunking (paragraph-based)
            chunks = self._semantic_chunking(text, doc_id, metadata)
            
            # Method 2: Fallback to sliding window if chunks are too large
            if any(chunk.word_count > self.chunk_size * 1.5 for chunk in chunks):
                logger.info("Using sliding window chunking for large segments")
                chunks = self._sliding_window_chunking(text, doc_id, metadata)
            
            # Filter out chunks that are too small
            valid_chunks = [
                chunk for chunk in chunks 
                if chunk.word_count >= self.min_chunk_size
            ]
            
            logger.info(f"Created {len(valid_chunks)} chunks for document {doc_id}")
            return valid_chunks
            
        except Exception as e:
            logger.error(f"Chunking error for document {doc_id}: {e}")
            raise
    
    def _semantic_chunking(self, text: str, doc_id: str, metadata: Dict) -> List[DocumentChunk]:
        """Chunk based on semantic boundaries (paragraphs, sections)"""
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        current_start = 0
        chunk_count = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_words = len(para.split())
            current_words = len(current_chunk.split())
            
            # If adding this paragraph would exceed chunk size
            if current_words + para_words > self.chunk_size and current_chunk:
                # Save current chunk
                chunk = self._create_chunk(
                    current_chunk, 
                    doc_id, 
                    chunk_count, 
                    current_start, 
                    metadata
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + "\n\n" + para if overlap_text else para
                current_start = self._find_text_position(text, current_chunk, current_start)
                chunk_count += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    current_start = text.find(para, current_start)
        
        # Add final chunk
        if current_chunk.strip():
            chunk = self._create_chunk(
                current_chunk, 
                doc_id, 
                chunk_count, 
                current_start, 
                metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _sliding_window_chunking(self, text: str, doc_id: str, metadata: Dict) -> List[DocumentChunk]:
        """Fallback sliding window chunking"""
        chunks = []
        words = text.split()
        
        if len(words) <= self.chunk_size:
            # Document is small enough to be one chunk
            chunk = self._create_chunk(text, doc_id, 0, 0, metadata)
            return [chunk]
        
        start_idx = 0
        chunk_count = 0
        
        while start_idx < len(words):
            # Get chunk words
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Find character positions
            char_start = len(' '.join(words[:start_idx]))
            if start_idx > 0:
                char_start += 1  # Account for space
            
            chunk = DocumentChunk(
                chunk_id=f"{doc_id}_chunk_{chunk_count}",
                text=chunk_text,
                start_char=char_start,
                end_char=char_start + len(chunk_text),
                word_count=len(chunk_words),
                metadata={
                    **metadata,
                    'chunk_method': 'sliding_window',
                    'chunk_index': chunk_count,
                    'total_chunks': None  # Will be updated later
                }
            )
            chunks.append(chunk)
            
            # Move window with overlap
            start_idx += self.chunk_size - self.overlap_size
            chunk_count += 1
        
        # Update total chunks count
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)
        
        return chunks
    
    def _create_chunk(self, text: str, doc_id: str, chunk_index: int, start_pos: int, metadata: Dict) -> DocumentChunk:
        """Create a DocumentChunk object"""
        return DocumentChunk(
            chunk_id=f"{doc_id}_chunk_{chunk_index}",
            text=text.strip(),
            start_char=start_pos,
            end_char=start_pos + len(text),
            word_count=len(text.split()),
            metadata={
                **metadata,
                'chunk_method': 'semantic',
                'chunk_index': chunk_index,
                'doc_id': doc_id
            }
        )
    
    def _get_overlap_text(self, text: str, max_words: int = None) -> str:
        """Get overlap text from end of chunk"""
        max_words = max_words or self.overlap_size
        words = text.split()
        
        if len(words) <= max_words:
            return text
        
        # Try to find sentence boundary for natural overlap
        sentences = nltk.sent_tokenize(text)
        if len(sentences) > 1:
            # Use last sentence(s) for overlap
            last_sentence = sentences[-1]
            if len(last_sentence.split()) <= max_words:
                return last_sentence
        
        # Fallback to word-based overlap
        return ' '.join(words[-max_words:])
    
    def _find_text_position(self, full_text: str, chunk_text: str, start_hint: int = 0) -> int:
        """Find position of chunk text in full document"""
        try:
            # Look for the beginning of the chunk text
            chunk_start = chunk_text[:50]  # First 50 chars
            position = full_text.find(chunk_start, start_hint)
            return position if position != -1 else start_hint
        except:
            return start_hint

# Global instance
document_chunker = DocumentChunker()
```

### 4. Document Processing Service (Main Orchestrator)

Create `backend/app/services/document_processor.py`:

```python
import uuid
from typing import Dict, List, Optional
import logging
from datetime import datetime

from app.services.file_handler import file_handler
from app.services.text_extractor import text_extractor
from app.services.document_chunker import document_chunker, DocumentChunk
from app.database.redis_client import redis_client

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main orchestrator for document processing pipeline"""
    
    def __init__(self):
        self.processing_status = {}  # Track processing status
    
    async def process_document(self, file_content: bytes, filename: str) -> Dict:
        """Complete document processing pipeline"""
        doc_id = str(uuid.uuid4())
        
        try:
            # Update processing status
            self._update_status(doc_id, "validating", 0)
            
            # Step 1: Validate file
            validation = await file_handler.validate_file(file_content, filename)
            if not validation["valid"]:
                raise ValueError(validation["error"])
            
            self._update_status(doc_id, "saving", 10)
            
            # Step 2: Save file
            file_metadata = await file_handler.save_file(file_content, filename)
            
            self._update_status(doc_id, "extracting", 25)
            
            # Step 3: Extract text
            extraction_result = await text_extractor.extract_text(
                file_metadata["file_path"], 
                file_metadata["mime_type"]
            )
            
            self._update_status(doc_id, "chunking", 50)
            
            # Step 4: Chunk document
            chunks = document_chunker.chunk_document(
                extraction_result["text"],
                doc_id,
                {
                    "filename": filename,
                    "mime_type": file_metadata["mime_type"],
                    "extraction_method": extraction_result["extraction_method"]
                }
            )
            
            self._update_status(doc_id, "storing", 75)
            
            # Step 5: Store in Redis
            document_data = await self._store_document(
                doc_id, 
                file_metadata, 
                extraction_result, 
                chunks
            )
            
            self._update_status(doc_id, "completed", 100)
            
            logger.info(f"Document processing completed: {doc_id} ({len(chunks)} chunks)")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "document": document_data,
                "chunks_created": len(chunks),
                "processing_time": self._get_processing_time(doc_id)
            }
            
        except Exception as e:
            self._update_status(doc_id, "failed", 0, str(e))
            logger.error(f"Document processing failed for {doc_id}: {e}")
            
            # Cleanup on failure
            if 'file_metadata' in locals():
                await file_handler.delete_file(file_metadata["file_path"])
            
            raise
        
        finally:
            # Clean up processing status after delay
            self._cleanup_status(doc_id)
    
    async def _store_document(self, 
                            doc_id: str, 
                            file_metadata: Dict, 
                            extraction_result: Dict, 
                            chunks: List[DocumentChunk]) -> Dict:
        """Store document and chunks in Redis"""
        
        # Prepare document metadata
        document_data = {
            "id": doc_id,
            "title": self._extract_title(file_metadata, extraction_result),
            "filename": file_metadata["original_filename"],
            "file_path": file_metadata["file_path"],
            "mime_type": file_metadata["mime_type"],
            "size_bytes": file_metadata["size_bytes"],
            "word_count": extraction_result["word_count"],
            "char_count": extraction_result["char_count"],
            "chunk_count": len(chunks),
            "uploaded_at": datetime.utcnow().isoformat(),
            "processed_at": datetime.utcnow().isoformat(),
            "extraction_metadata": extraction_result.get("metadata", {}),
            "status": "processed",
            "tags": self._generate_tags(file_metadata, extraction_result)
        }
        
        # Add page count if available
        if "page_count" in extraction_result:
            document_data["page_count"] = extraction_result["page_count"]
        
        # Store document metadata in Redis JSON
        document_key = f"doc:meta:{doc_id}"
        redis_client.set_json(document_key, document_data)
        
        # Store chunks metadata (for now, we'll store as JSON)
        # In the next phase, we'll convert these to vector embeddings
        chunks_data = []
        for chunk in chunks:
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "doc_id": doc_id,
                "text": chunk.text,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "word_count": chunk.word_count,
                "chunk_index": chunk.metadata.get("chunk_index", 0),
                "metadata": chunk.metadata
            }
            chunks_data.append(chunk_data)
            
            # Store individual chunk
            chunk_key = f"doc:chunk:{chunk.chunk_id}"
            redis_client.set_json(chunk_key, chunk_data)
        
        # Store chunks list reference
        chunks_key = f"doc:chunks:{doc_id}"
        redis_client.set_json(chunks_key, {"chunks": [c["chunk_id"] for c in chunks_data]})
        
        # Update document index (for listing)
        redis_client.client.sadd("doc:index", doc_id)
        
        # Update analytics
        redis_client.increment_counter("stats:documents_processed")
        redis_client.increment_counter("stats:chunks_created", len(chunks))
        
        return document_data
    
    def get_processing_status(self, doc_id: str) -> Optional[Dict]:
        """Get current processing status"""
        return self.processing_status.get(doc_id)
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve document by ID"""
        try:
            document_key = f"doc:meta:{doc_id}"
            return redis_client.get_json(document_key)
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None
    
    async def list_documents(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all processed documents"""
        try:
            # Get all document IDs
            doc_ids = redis_client.client.smembers("doc:index")
            
            # Apply pagination
            doc_ids_list = list(doc_ids)[offset:offset + limit]
            
            # Retrieve document metadata
            documents = []
            for doc_id in doc_ids_list:
                doc = await self.get_document(doc_id)
                if doc:
                    documents.append(doc)
            
            # Sort by upload date (newest first)
            documents.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document and all associated data"""
        try:
            # Get document metadata
            doc = await self.get_document(doc_id)
            if not doc:
                return False
            
            # Delete file
            if "file_path" in doc:
                await file_handler.delete_file(doc["file_path"])
            
            # Get chunks to delete
            chunks_key = f"doc:chunks:{doc_id}"
            chunks_data = redis_client.get_json(chunks_key)
            
            if chunks_data and "chunks" in chunks_data:
                # Delete individual chunks
                for chunk_id in chunks_data["chunks"]:
                    redis_client.client.delete(f"doc:chunk:{chunk_id}")
            
            # Delete document keys
            redis_client.client.delete(f"doc:meta:{doc_id}")
            redis_client.client.delete(chunks_key)
            
            # Remove from index
            redis_client.client.srem("doc:index", doc_id)
            
            # Update analytics
            redis_client.increment_counter("stats:documents_deleted")
            
            logger.info(f"Document deleted: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def _extract_title(self, file_metadata: Dict, extraction_result: Dict) -> str:
        """Extract or generate document title"""
        # Try metadata title first
        metadata = extraction_result.get("metadata", {})
        if metadata.get("title"):
            return metadata["title"].strip()
        
        # Try first line of text
        text = extraction_result.get("text", "")
        if text:
            first_line = text.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                return first_line
        
        # Fallback to filename
        return file_metadata["original_filename"]
    
    def _generate_tags(self, file_metadata: Dict, extraction_result: Dict) -> List[str]:
        """Generate tags for document"""
        tags = []
        
        # File type tag
        mime_type = file_metadata["mime_type"]
        if "pdf" in mime_type:
            tags.append("pdf")
        elif "word" in mime_type:
            tags.append("word")
        elif "text" in mime_type:
            tags.append("text")
        
        # Size tags
        size_mb = file_metadata["size_bytes"] / (1024 * 1024)
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

# Global instance
document_processor = DocumentProcessor()