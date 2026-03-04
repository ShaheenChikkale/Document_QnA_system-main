"""
Smart Text Chunking with Overlap
Implements intelligent document chunking for optimal retrieval
"""
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


class SmartChunker:
    """Intelligent text chunking with context preservation"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter with smart separators
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Multiple newlines (major sections)
                "\n\n",    # Paragraph breaks
                "\n",      # Single newlines
                ". ",      # Sentences
                "! ",
                "? ",
                "; ",
                ", ",
                " ",       # Words
                ""         # Characters
            ],
            keep_separator=True
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text to chunk
            metadata: Additional metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for idx, chunk_text in enumerate(chunks):
            chunk_obj = {
                "text": chunk_text.strip(),
                "chunk_index": idx,
                "char_count": len(chunk_text),
                **(metadata or {})
            }
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def chunk_with_context(
        self,
        text: str,
        metadata: Dict[str, Any] = None,
        context_window: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Chunk text with surrounding context
        
        Args:
            text: Text to chunk
            metadata: Additional metadata
            context_window: Characters of context to include before/after
            
        Returns:
            List of chunks with context
        """
        chunks = self.chunk_text(text, metadata)
        
        # Add context to each chunk
        for chunk in chunks:
            start_idx = chunk.get('chunk_index', 0)
            
            # Add previous chunk context
            if start_idx > 0:
                prev_chunk = chunks[start_idx - 1]
                chunk['context_before'] = prev_chunk['text'][-context_window:]
            
            # Add next chunk context
            if start_idx < len(chunks) - 1:
                next_chunk = chunks[start_idx + 1]
                chunk['context_after'] = next_chunk['text'][:context_window]
        
        return chunks


def create_chunker(chunk_size: int = 500, chunk_overlap: int = 100) -> SmartChunker:
    """Factory function to create a chunker instance"""
    return SmartChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
