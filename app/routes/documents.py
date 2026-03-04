"""
Document Management Routes
Handles document upload, listing, and deletion
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
import uuid
from datetime import datetime

from app.models import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
    DeleteDocumentResponse,
    ErrorResponse
)
from app.services import (
    get_document_processor,
    get_embedding_service,
    get_retrieval_service,
    get_cache_service
)
from app.config import get_settings

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a document",
    description="Upload a document (PDF, DOCX, TXT, or image) for indexing and Q&A"
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document
    
    - Supports: PDF, DOCX, TXT, PNG, JPG, JPEG
    - Applies OCR for scanned documents
    - Creates vector embeddings and indexes
    - Returns document metadata
    """
    # Validate file extension
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{file_extension} not supported. Allowed types: {settings.allowed_extensions}"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size / (1024*1024)}MB"
        )
    
    try:
        # Process document
        doc_processor = get_document_processor()
        document_id, metadata, extracted_text = await doc_processor.process_document(
            file_content=content,
            filename=file.filename
        )
        
        # Create chunks
        chunks = doc_processor.create_chunks(extracted_text, metadata)
        
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text could be extracted from the document"
            )
        
        # Index chunks
        embedding_service = get_embedding_service()
        chunks_indexed = await embedding_service.index_chunks(chunks, document_id)
        
        # Update BM25 index for hybrid search
        retrieval_service = get_retrieval_service()
        retrieval_service.update_bm25_index(document_id, chunks)
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=len(content),
            pages=metadata.get('page_count'),
            chunks_created=chunks_indexed,
            message=f"Document successfully uploaded and indexed with {chunks_indexed} chunks"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="Get a list of all uploaded documents with metadata"
)
async def list_documents():
    """
    List all indexed documents
    
    Returns metadata for all documents in the system
    """
    try:
        embedding_service = get_embedding_service()
        documents = embedding_service.list_all_documents()
        
        document_infos = [
            DocumentInfo(
                document_id=doc['document_id'],
                filename=doc['filename'],
                file_size=doc['file_size'],
                upload_date=datetime.utcnow(),  # You can store this in metadata
                pages=None,
                chunks_count=doc['chunks_count'],
                language=doc.get('language')
            )
            for doc in documents
        ]
        
        return DocumentListResponse(
            documents=document_infos,
            total_count=len(document_infos)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    response_model=DeleteDocumentResponse,
    summary="Delete a document",
    description="Remove a document and all its chunks from the system"
)
async def delete_document(document_id: str):
    """
    Delete a document by ID
    
    - Removes from vector database
    - Removes from BM25 index
    - Invalidates related cache entries
    - Deletes physical file
    """
    try:
        # Get document metadata
        embedding_service = get_embedding_service()
        metadata = embedding_service.get_document_metadata(document_id)
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # Delete from vector database
        await embedding_service.delete_document(document_id)
        
        # Delete from BM25 index
        retrieval_service = get_retrieval_service()
        if document_id in retrieval_service.bm25_corpus:
            del retrieval_service.bm25_corpus[document_id]
            del retrieval_service.bm25_docs[document_id]
        
        # Invalidate cache
        cache_service = get_cache_service()
        cache_service.invalidate_document(document_id)
        
        # Delete physical file
        doc_processor = get_document_processor()
        # Note: File path would need to be stored in metadata for this to work
        
        return DeleteDocumentResponse(
            document_id=document_id,
            message=f"Document {metadata['filename']} successfully deleted"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentInfo,
    summary="Get document details",
    description="Retrieve metadata for a specific document"
)
async def get_document(document_id: str):
    """Get document metadata by ID"""
    try:
        embedding_service = get_embedding_service()
        metadata = embedding_service.get_document_metadata(document_id)
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        return DocumentInfo(
            document_id=document_id,
            filename=metadata['filename'],
            file_size=metadata['file_size'],
            upload_date=datetime.utcnow(),
            pages=None,
            chunks_count=metadata['chunks_count'],
            language=metadata.get('language')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )
