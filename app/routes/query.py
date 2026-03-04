"""
Query Routes
Handles Q&A queries and conversation memory management
"""
from fastapi import APIRouter, HTTPException, status
import uuid
import time

from app.models import (
    QueryRequest,
    QueryResponse,
    SourceDocument,
    ClearMemoryResponse
)
from app.services import (
    get_retrieval_service,
    get_llm_service,
    get_cache_service
)
from app.config import get_settings

router = APIRouter(prefix="/query", tags=["Query"])
settings = get_settings()


@router.post(
    "",
    response_model=QueryResponse,
    summary="Ask a question",
    description="Query the document knowledge base with conversational memory support"
)
async def query_documents(request: QueryRequest):
    """
    Query documents with intelligent retrieval and answer generation
    
    Features:
    - Hybrid search (vector + BM25)
    - Cross-encoder reranking
    - Conversational memory for follow-up questions
    - Query result caching
    - Source attribution
    
    Args:
        request: Query request with question and optional parameters
        
    Returns:
        Answer with source documents and metadata
    """
    start_time = time.time()
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Check cache first
    cache_service = get_cache_service()
    cached_result = cache_service.get(
        query=request.question,
        document_id=None,
        top_k=request.top_k
    )
    
    if cached_result:
        cached_result['cached'] = True
        cached_result['processing_time'] = time.time() - start_time
        return QueryResponse(**cached_result)
    
    try:
        # Step 1: Retrieve relevant documents with hybrid search + reranking
        retrieval_service = get_retrieval_service()
        retrieved_docs = await retrieval_service.retrieve_with_reranking(
            query=request.question,
            top_k_retrieval=settings.top_k_retrieval,
            top_k_final=request.top_k
        )
        
        if not retrieved_docs:
            return QueryResponse(
                answer="I couldn't find any relevant documents to answer your question. Please try rephrasing or upload relevant documents first.",
                sources=[],
                session_id=session_id,
                processing_time=time.time() - start_time,
                cached=False
            )
        
        # Step 2: Generate answer using LLM with conversation memory
        llm_service = get_llm_service()
        answer_result = await llm_service.generate_answer_with_citations(
            question=request.question,
            context_documents=retrieved_docs,
            session_id=session_id
        )
        
        # Step 3: Format source documents
        sources = []
        if request.include_sources:
            for doc in retrieved_docs:
                sources.append(SourceDocument(
                    document_id=doc.get('document_id', ''),
                    filename=doc.get('filename', 'Unknown'),
                    page=doc.get('page'),
                    chunk_id=doc.get('chunk_id', ''),
                    relevance_score=doc.get('rerank_score', doc.get('score', 0)),
                    content=doc['text'][:500]  # Limit content length
                ))
        
        # Create response
        response_data = {
            "answer": answer_result['answer'],
            "sources": sources,
            "session_id": session_id,
            "processing_time": time.time() - start_time,
            "cached": False
        }
        
        # Cache the result
        cache_service.set(
            query=request.question,
            result=response_data,
            top_k=request.top_k
        )
        
        return QueryResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post(
    "/clear-memory",
    response_model=ClearMemoryResponse,
    summary="Clear conversation memory",
    description="Reset conversation history for a session or all sessions"
)
async def clear_conversation_memory(session_id: str = None):
    """
    Clear conversation memory
    
    Args:
        session_id: Optional session ID to clear. If not provided, clears all sessions.
        
    Returns:
        Confirmation message
    """
    try:
        llm_service = get_llm_service()
        llm_service.clear_memory(session_id)
        
        message = f"Conversation memory cleared for session {session_id}" if session_id else "All conversation memories cleared"
        
        return ClearMemoryResponse(
            session_id=session_id,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear memory: {str(e)}"
        )


@router.get(
    "/history/{session_id}",
    summary="Get conversation history",
    description="Retrieve conversation history for a session"
)
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of conversation turns
    """
    try:
        llm_service = get_llm_service()
        history = llm_service.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "turn_count": len(history)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation history: {str(e)}"
        )


@router.get(
    "/cache-stats",
    summary="Get cache statistics",
    description="Retrieve cache performance metrics"
)
async def get_cache_stats():
    """
    Get cache statistics
    
    Returns:
        Cache performance metrics including hit rate
    """
    try:
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        
        return {
            "cache_statistics": stats,
            "description": "Cache performance metrics"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache stats: {str(e)}"
        )
