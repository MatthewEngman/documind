import os
import hashlib
import aiofiles
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import re

from app.config import settings

# Fallback MIME type detection (python-magic alternative)
def get_mime_type_fallback(file_content: bytes, filename: str) -> str:
    """Fallback MIME type detection based on file extension and content"""
    file_ext = Path(filename).suffix.lower()
    
    # Basic MIME type mapping
    mime_map = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.rtf': 'application/rtf'
    }
    
    # Try to detect based on file signature (magic bytes)
    if file_content.startswith(b'%PDF'):
        return 'application/pdf'
    elif file_content.startswith(b'PK\x03\x04') and file_ext == '.docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif file_content.startswith(b'{\\rtf'):
        return 'application/rtf'
    
    # Fall back to extension-based detection
    return mime_map.get(file_ext, 'application/octet-stream')

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles file operations, validation, and metadata extraction"""
    
    def __init__(self):
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
            
            # Check file type using fallback detection
            mime_type = get_mime_type_fallback(file_content, filename)
            
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
                "mime_type": get_mime_type_fallback(file_content, filename)
            }
            
            logger.info(f"File saved: {unique_filename} ({len(file_content)} bytes)")
            return metadata
            
        except Exception as e:
            logger.error(f"File save error: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace unsafe characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(safe_name) > 100:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:95] + ext
        return safe_name
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
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
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                "path": str(path),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"File info error: {e}")
            return None

# Global instance
file_handler = FileHandler()
