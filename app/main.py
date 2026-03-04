"""
FastAPI Main Application
Production-grade Document Q&A System
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import get_settings
from app.routes import documents_router, query_router
from app.models import HealthResponse, ErrorResponse
from app.services import (
    get_embedding_service,
    get_retrieval_service,
    get_llm_service,
    get_cache_service
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("=" * 80)
    print("Starting Document Q&A System")
    print("=" * 80)
    
    # Initialize services
    print("Initializing services...")
    embedding_service = get_embedding_service()
    retrieval_service = get_retrieval_service()
    llm_service = get_llm_service()
    cache_service = get_cache_service()
    
    print("✓ Embedding service initialized")
    print("✓ Retrieval service initialized")
    print("✓ LLM service initialized")
    print("✓ Cache service initialized")
    print("=" * 80)
    print(f"Server ready at http://{settings.host}:{settings.port}")
    print("=" * 80)
    
    yield
    
    # Shutdown
    print("\nShutting down Document Q&A System...")


# Create FastAPI application
app = FastAPI(
    title="Document Q&A System",
    description="""
    Production-grade intelligent document Q&A system with advanced retrieval.
    
    ## Features
    - **Hybrid Search**: Combines vector similarity and BM25 keyword search
    - **Reranking**: Cross-encoder reranking for improved accuracy
    - **Multilingual Support**: Process documents in multiple languages
    - **OCR**: Extract text from scanned PDFs and images
    - **Conversational Memory**: Handle follow-up questions with context
    - **Smart Caching**: Cache frequent queries for faster responses
    - **Source Attribution**: Cite specific documents and pages
    
    ## Supported Formats
    - PDF (including scanned documents)
    - DOCX
    - TXT
    - Images (PNG, JPG, JPEG)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc)
        ).model_dump()
    )


# Include routers
app.include_router(documents_router)
app.include_router(query_router)


# Serve UI
ui_dir = Path(__file__).parent.parent / "ui"
if ui_dir.exists():
    @app.get("/ui", include_in_schema=False)
    async def serve_ui():
        """Serve the web UI"""
        return FileResponse(ui_dir / "index.html")
    
    # Mount static files if needed
    try:
        app.mount("/ui/static", StaticFiles(directory=str(ui_dir)), name="ui_static")
    except:
        pass


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Check system health and service status"
)
async def health_check():
    """
    Health check endpoint
    
    Returns system status and service availability
    """
    try:
        # Check services
        embedding_service = get_embedding_service()
        cache_service = get_cache_service()
        
        services = {
            "embedding_service": "healthy",
            "vector_database": "healthy",
            "llm_service": "healthy",
            "cache_service": "healthy"
        }
        
        cache_stats = cache_service.get_stats()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            services=services
        )
    
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            services={"error": str(e)}
        )


@app.get(
    "/",
    tags=["System"],
    summary="Root endpoint",
    description="API information and links"
)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Document Q&A System API",
        "version": "1.0.0",
        "ui": "/ui",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "features": [
            "Hybrid Search (Vector + BM25)",
            "Cross-encoder Reranking",
            "Multilingual Support",
            "OCR for Scanned Documents",
            "Conversational Memory",
            "Query Caching",
            "Source Attribution"
        ],
        "endpoints": {
            "upload_document": "POST /documents/upload",
            "list_documents": "GET /documents",
            "delete_document": "DELETE /documents/{document_id}",
            "query": "POST /query",
            "clear_memory": "POST /query/clear-memory",
            "conversation_history": "GET /query/history/{session_id}",
            "cache_stats": "GET /query/cache-stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
