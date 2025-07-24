"""
File handling utilities
"""
import os
import shutil
import tempfile
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import mimetypes
import hashlib
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class FileHandler:
    """Utility class for file operations"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.temp_dir = Path(tempfile.gettempdir()) / "documind"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directories ensured: {self.upload_dir}, {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
    
    def save_uploaded_file(self, content: bytes, filename: str, document_id: str) -> str:
        """
        Save uploaded file to disk
        """
        try:
            # Create document-specific directory
            doc_dir = self.upload_dir / document_id
            doc_dir.mkdir(exist_ok=True)
            
            # Save file
            file_path = doc_dir / filename
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            stat = path.stat()
            
            return {
                "filename": path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": path.suffix.lower(),
                "mime_type": mimetypes.guess_type(str(path))[0],
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK),
                "absolute_path": str(path.absolute())
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {}
    
    def calculate_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """
        Calculate hash of file content
        """
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file
        """
        try:
            path = Path(file_path)
            
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                
                # Clean up empty directory
                try:
                    if path.parent != self.upload_dir and not any(path.parent.iterdir()):
                        path.parent.rmdir()
                        logger.info(f"Empty directory removed: {path.parent}")
                except:
                    pass  # Ignore directory cleanup errors
                
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def create_temp_file(self, content: bytes, suffix: str = "") -> str:
        """
        Create a temporary file with content
        """
        try:
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.temp_dir,
                suffix=suffix,
                delete=False
            )
            
            temp_file.write(content)
            temp_file.close()
            
            logger.debug(f"Temporary file created: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to create temporary file: {e}")
            raise
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files
        """
        try:
            if not self.temp_dir.exists():
                return 0
            
            current_time = datetime.now()
            deleted_count = 0
            
            for file_path in self.temp_dir.iterdir():
                try:
                    if file_path.is_file():
                        file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_age.total_seconds() > max_age_hours * 3600:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Deleted old temp file: {file_path}")
                            
                except Exception as e:
                    logger.warning(f"Failed to process temp file {file_path}: {e}")
                    continue
            
            logger.info(f"Cleaned up {deleted_count} temporary files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
            return 0
    
    def validate_file_type(self, filename: str) -> Dict[str, Any]:
        """
        Validate file type against allowed extensions
        """
        try:
            path = Path(filename)
            extension = path.suffix.lower()
            
            is_allowed = extension in settings.allowed_extensions
            mime_type = mimetypes.guess_type(filename)[0]
            
            return {
                "filename": filename,
                "extension": extension,
                "mime_type": mime_type,
                "is_allowed": is_allowed,
                "allowed_extensions": list(settings.allowed_extensions)
            }
            
        except Exception as e:
            logger.error(f"File type validation failed for {filename}: {e}")
            return {
                "filename": filename,
                "is_allowed": False,
                "error": str(e)
            }
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """
        Get storage usage statistics
        """
        try:
            total_size = 0
            file_count = 0
            type_distribution = {}
            
            if self.upload_dir.exists():
                for file_path in self.upload_dir.rglob("*"):
                    if file_path.is_file():
                        try:
                            size = file_path.stat().st_size
                            total_size += size
                            file_count += 1
                            
                            extension = file_path.suffix.lower()
                            type_distribution[extension] = type_distribution.get(extension, 0) + 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to process file {file_path}: {e}")
                            continue
            
            return {
                "total_size_bytes": total_size,
                "total_size_human": self._format_bytes(total_size),
                "file_count": file_count,
                "type_distribution": type_distribution,
                "upload_directory": str(self.upload_dir),
                "last_calculated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate storage usage: {e}")
            return {
                "error": "Failed to calculate storage usage",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes into human readable format
        """
        try:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        except:
            return f"{bytes_value} B"
    
    def backup_file(self, file_path: str, backup_dir: Optional[str] = None) -> str:
        """
        Create a backup copy of a file
        """
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            # Use provided backup directory or create one
            if backup_dir:
                backup_path = Path(backup_dir)
            else:
                backup_path = self.upload_dir / "backups"
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_file_path = backup_path / backup_filename
            
            # Copy file
            shutil.copy2(source_path, backup_file_path)
            
            logger.info(f"File backed up: {file_path} -> {backup_file_path}")
            return str(backup_file_path)
            
        except Exception as e:
            logger.error(f"File backup failed for {file_path}: {e}")
            raise
    
    def list_files(self, directory: Optional[str] = None, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in directory with optional pattern matching
        """
        try:
            search_dir = Path(directory) if directory else self.upload_dir
            
            if not search_dir.exists():
                return []
            
            files = []
            for file_path in search_dir.glob(pattern):
                if file_path.is_file():
                    try:
                        file_info = self.get_file_info(str(file_path))
                        files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for {file_path}: {e}")
                        continue
            
            return sorted(files, key=lambda x: x.get('modified', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []

# Global file handler instance
file_handler = FileHandler()
