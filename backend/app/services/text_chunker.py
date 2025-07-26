import re
import uuid
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TextChunker:
    """Intelligent text chunking for optimal search and retrieval"""
    
    def __init__(self, 
                 max_chunk_size: int = 1000,
                 min_chunk_size: int = 100,
                 overlap_size: int = 50):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size
    
    async def chunk_text(self, text: str, doc_id: str, metadata: Dict) -> List[Dict]:
        """Chunk text intelligently based on content structure"""
        try:
            if not text or not text.strip():
                return []
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Try different chunking strategies based on text structure
            chunks = []
            
            # Strategy 1: Paragraph-based chunking (preferred)
            paragraph_chunks = self._chunk_by_paragraphs(cleaned_text)
            if paragraph_chunks:
                chunks = paragraph_chunks
            else:
                # Strategy 2: Sentence-based chunking (fallback)
                sentence_chunks = self._chunk_by_sentences(cleaned_text)
                if sentence_chunks:
                    chunks = sentence_chunks
                else:
                    # Strategy 3: Fixed-size chunking (last resort)
                    chunks = self._chunk_by_size(cleaned_text)
            
            # Create chunk objects with metadata
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                if len(chunk_text.strip()) < self.min_chunk_size:
                    continue
                
                start_pos = 0
                if i > 0:
                    start_pos = sum(len(chunks[j]) for j in range(i))
                
                chunk_obj = {
                    "chunk_id": str(uuid.uuid4()),
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunk_text.strip(),
                    "word_count": len(chunk_text.split()),
                    "char_count": len(chunk_text),
                    "start_char": start_pos,
                    "end_char": start_pos + len(chunk_text),
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source_filename": metadata.get("filename", "unknown"),
                        "chunk_method": self._get_chunk_method(chunk_text),
                        "position_in_document": i / len(chunks) if chunks else 0,
                        "has_overlap": i > 0  # All chunks except first have overlap
                    }
                }
                chunk_objects.append(chunk_obj)
            
            logger.info(f"Created {len(chunk_objects)} chunks for document {doc_id}")
            return chunk_objects
            
        except Exception as e:
            logger.error(f"Text chunking error for {doc_id}: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines but preserve paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Clean up common artifacts
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\\n\r]', '', text)
        
        return text.strip()
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk text by paragraphs, combining small ones"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max size, save current chunk
            if current_chunk and len(current_chunk) + len(paragraph) > self.max_chunk_size:
                chunks.append(current_chunk)
                # Start new chunk with overlap from previous chunk
                current_chunk = self._get_overlap(current_chunk) + paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text by sentences when paragraph structure is unclear"""
        # Simple sentence splitting (could be improved with NLTK)
        sentences = re.split(r'[.!?]+\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed max size, save current chunk
            if current_chunk and len(current_chunk) + len(sentence) > self.max_chunk_size:
                chunks.append(current_chunk)
                # Start new chunk with overlap
                current_chunk = self._get_overlap(current_chunk) + sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_size(self, text: str) -> List[str]:
        """Fixed-size chunking as last resort"""
        chunks = []
        words = text.split()
        
        if not words:
            return []
        
        current_chunk_words = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > self.max_chunk_size and current_chunk_words:
                # Save current chunk
                chunk_text = " ".join(current_chunk_words)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_words = current_chunk_words[-self.overlap_size//10:] if len(current_chunk_words) > self.overlap_size//10 else []
                current_chunk_words = overlap_words + [word]
                current_size = sum(len(w) + 1 for w in current_chunk_words)
            else:
                current_chunk_words.append(word)
                current_size += word_size
        
        # Add final chunk
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            chunks.append(chunk_text)
        
        return chunks
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of a chunk"""
        words = text.split()
        if len(words) <= self.overlap_size // 10:
            return ""
        
        overlap_words = words[-(self.overlap_size // 10):]
        return " ".join(overlap_words) + " "
    
    def _get_chunk_method(self, chunk_text: str) -> str:
        """Determine the chunking method used based on chunk characteristics"""
        if '\n\n' in chunk_text:
            return "paragraph"
        elif '. ' in chunk_text and chunk_text.count('. ') > 2:
            return "sentence"
        else:
            return "fixed_size"
    
    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """Get statistics about the chunks"""
        if not chunks:
            return {
                "total_chunks": 0,
                "total_words": 0,
                "total_chars": 0,
                "avg_words_per_chunk": 0,
                "avg_chars_per_chunk": 0
            }
        
        total_words = sum(chunk["word_count"] for chunk in chunks)
        total_chars = sum(chunk["char_count"] for chunk in chunks)
        
        return {
            "total_chunks": len(chunks),
            "total_words": total_words,
            "total_chars": total_chars,
            "avg_words_per_chunk": total_words / len(chunks),
            "avg_chars_per_chunk": total_chars / len(chunks),
            "min_words": min(chunk["word_count"] for chunk in chunks),
            "max_words": max(chunk["word_count"] for chunk in chunks)
        }

# Global instance
text_chunker = TextChunker()
