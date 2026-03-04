"""
Embedding Service
Handles vector embeddings and Pinecone operations
"""
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import pinecone
from pinecone import Pinecone, ServerlessSpec
import hashlib

from app.config import get_settings


class EmbeddingService:
    """Manages embeddings and vector database operations"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize embedding model
        print(f"Loading embedding model: {self.settings.embedding_model}")
        self.embedding_model = SentenceTransformer(self.settings.embedding_model)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self._initialize_index()
        
        # Document metadata storage
        self.documents_metadata = {}
    
    def _initialize_index(self):
        """Initialize or connect to Pinecone index"""
        index_name = self.settings.pinecone_index_name
        
        # Check if index exists
        existing_indexes = self.pc.list_indexes()
        index_names = [idx['name'] for idx in existing_indexes]
        
        if index_name not in index_names:
            print(f"Creating new Pinecone index: {index_name}")
            self.pc.create_index(
                name=index_name,
                dimension=self.embedding_dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        # Connect to index
        self.index = self.pc.Index(index_name)
        print(f"Connected to Pinecone index: {index_name}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    async def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_id: str
    ) -> int:
        """
        Index document chunks into Pinecone
        
        Args:
            chunks: List of chunk dictionaries
            document_id: Unique document identifier
            
        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        
        # Prepare vectors for upsert
        vectors = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}_chunk_{idx}"
            
            metadata = {
                "document_id": document_id,
                "chunk_index": idx,
                "text": chunk['text'][:1000],  # Store truncated text
                "filename": chunk.get('filename', ''),
                "page": chunk.get('page_count'),
                "char_count": chunk.get('char_count', 0)
            }
            
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": metadata
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
        
        # Store document metadata
        self.documents_metadata[document_id] = {
            "filename": chunks[0].get('filename', ''),
            "chunks_count": len(chunks),
            "file_size": chunks[0].get('file_size', 0),
            "language": chunks[0].get('language', 'unknown')
        }
        
        return len(chunks)
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            document_id: Optional filter by document ID
            
        Returns:
            List of matching chunks with scores
        """
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Build filter
        filter_dict = {}
        if document_id:
            filter_dict["document_id"] = document_id
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        # Format results
        matches = []
        for match in results.matches:
            matches.append({
                "chunk_id": match.id,
                "score": match.score,
                "text": match.metadata.get('text', ''),
                "document_id": match.metadata.get('document_id', ''),
                "filename": match.metadata.get('filename', ''),
                "page": match.metadata.get('page'),
                "metadata": match.metadata
            })
        
        return matches
    
    async def delete_document(self, document_id: str):
        """
        Delete all chunks for a document
        
        Args:
            document_id: Document ID to delete
        """
        # Delete from Pinecone using filter
        self.index.delete(filter={"document_id": document_id})
        
        # Remove from metadata
        if document_id in self.documents_metadata:
            del self.documents_metadata[document_id]
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a document"""
        return self.documents_metadata.get(document_id)
    
    def list_all_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents"""
        return [
            {"document_id": doc_id, **metadata}
            for doc_id, metadata in self.documents_metadata.items()
        ]


# Singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
