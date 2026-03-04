# System Architecture

## Overview

The Document Q&A System is built with a modular, production-ready architecture following best practices for scalability, maintainability, and performance.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Layer                          │
│  (Browser, cURL, Python, Mobile Apps, etc.)                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Middleware: CORS, Timing, Error Handling            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes: /documents, /query, /health                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Services Layer                          │
│  ┌──────────────┬──────────────┬───────────────┐          │
│  │  Document    │  Embedding   │  Retrieval    │          │
│  │  Processor   │  Service     │  Service      │          │
│  └──────────────┴──────────────┴───────────────┘          │
│  ┌──────────────┬──────────────┐                          │
│  │  LLM Service │ Cache Service│                          │
│  └──────────────┴──────────────┘                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   External Services                         │
│  ┌──────────────┬──────────────┬──────────────┐           │
│  │  Pinecone    │  Groq API    │  File System │           │
│  │  (Vector DB) │  (LLM)       │  (Storage)   │           │
│  └──────────────┴──────────────┴──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Gateway Layer

**Technology**: FastAPI

**Responsibilities**:
- Handle HTTP requests and responses
- Input validation using Pydantic models
- API documentation generation
- Error handling and logging
- CORS policy enforcement
- Request timing

**Key Features**:
- Async endpoints for better concurrency
- Automatic OpenAPI documentation
- Type safety with Pydantic
- Exception handling middleware

### 2. Services Layer

#### 2.1 Document Processor Service

**File**: `app/services/document_processor.py`

**Responsibilities**:
- Accept file uploads
- Extract text from various formats
- Apply OCR for scanned documents
- Detect document language
- Create document metadata

**Supported Formats**:
- PDF (regular and scanned)
- DOCX (Microsoft Word)
- TXT (plain text)
- Images (PNG, JPG, JPEG)

**Processing Pipeline**:
```
Upload → Format Detection → Text Extraction → OCR (if needed) 
→ Language Detection → Chunking → Metadata Creation
```

#### 2.2 Embedding Service

**File**: `app/services/embedding_service.py`

**Responsibilities**:
- Generate vector embeddings
- Manage Pinecone vector database
- Index document chunks
- Perform vector similarity search
- Handle document deletion

**Embedding Model**:
- Default: `paraphrase-multilingual-mpnet-base-v2`
- Dimension: 768
- Supports 50+ languages

**Pinecone Operations**:
- Index creation/connection
- Batch upsert (100 vectors/batch)
- Filtered queries
- Metadata storage

#### 2.3 Retrieval Service

**File**: `app/services/retrieval_service.py`

**Responsibilities**:
- Hybrid search (Vector + BM25)
- Cross-encoder reranking
- Result fusion
- Context optimization

**Retrieval Pipeline**:
```
Query → [Vector Search + BM25 Search] → Fusion (RRF) 
→ Cross-Encoder Reranking → Top-K Selection
```

**Hybrid Search**:
- **Vector Search**: Semantic similarity using embeddings
- **BM25 Search**: Keyword-based statistical ranking
- **Fusion**: Reciprocal Rank Fusion (RRF)
- **Weights**: 70% vector, 30% BM25 (configurable)

**Reranking**:
- Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Purpose: Re-score query-document pairs
- Improves precision significantly

#### 2.4 LLM Service

**File**: `app/services/llm_service.py`

**Responsibilities**:
- Generate answers using Groq API
- Manage conversation memory
- Format context from retrieved documents
- Handle source citations
- Maintain chat history

**LLM Integration**:
- Provider: Groq (ultra-fast inference)
- Model: Mixtral-8x7B (default)
- Temperature: 0.1 (factual answers)
- Max tokens: 1024

**Conversational Memory**:
- Type: ConversationBufferMemory (LangChain)
- Scope: Per-session
- History limit: 10 turns (configurable)
- Persistence: In-memory

**RAG Pipeline**:
```
Question + Context + History → Prompt Template 
→ LLM → Answer + Citations
```

#### 2.5 Cache Service

**File**: `app/services/cache_service.py`

**Responsibilities**:
- Cache query results
- LRU eviction policy
- Cache invalidation
- Performance metrics

**Caching Strategy**:
- Key: Hash of (query, document_id, top_k)
- Value: Complete query response
- Eviction: Least Recently Used (LRU)
- Size: 100 entries (configurable)

### 3. Utilities Layer

#### 3.1 Smart Chunking

**File**: `app/utils/chunking.py`

**Strategy**:
- Recursive character text splitting
- Chunk size: 500 characters (default)
- Overlap: 100 characters (default)
- Separator hierarchy: paragraphs → sentences → words

**Benefits**:
- Preserves context at chunk boundaries
- Maintains semantic coherence
- Improves retrieval accuracy

#### 3.2 OCR Processing

**File**: `app/utils/ocr.py`

**Technology**: Tesseract OCR

**Features**:
- Multi-language support
- Automatic language detection
- Scanned PDF handling
- Image text extraction

### 4. External Services

#### 4.1 Pinecone (Vector Database)

**Purpose**: Store and query vector embeddings

**Configuration**:
- Cloud: AWS / GCP (serverless)
- Metric: Cosine similarity
- Dimension: 768 (matches embedding model)
- Index: Single index for all documents

**Metadata Storage**:
```json
{
  "document_id": "abc123",
  "chunk_index": 5,
  "text": "chunk content...",
  "filename": "document.pdf",
  "page": 3,
  "char_count": 450
}
```

#### 4.2 Groq API (LLM Inference)

**Purpose**: Fast LLM inference for answer generation

**Benefits**:
- Ultra-low latency (< 1s inference)
- High throughput
- Multiple model options
- Cost-effective

**Available Models**:
- Mixtral-8x7B (balanced)
- Llama3-70B (high quality)
- Llama3-8B (fast)
- Gemma-7B (lightweight)

#### 4.3 File System

**Purpose**: Store uploaded documents

**Structure**:
```
data/
└── uploads/
    ├── {document_id}.pdf
    ├── {document_id}.docx
    └── ...
```

## Data Flow

### Document Upload Flow

```
1. Client uploads file
   ↓
2. API validates file (type, size)
   ↓
3. Document Processor extracts text
   ↓
4. Smart Chunker creates chunks
   ↓
5. Embedding Service generates vectors
   ↓
6. Pinecone stores vectors + metadata
   ↓
7. Retrieval Service updates BM25 index
   ↓
8. Return document_id to client
```

### Query Flow

```
1. Client sends question
   ↓
2. Cache Service checks for cached result
   ↓ (cache miss)
3. Retrieval Service performs hybrid search
   ├─ Vector search in Pinecone
   └─ BM25 search in local index
   ↓
4. Fusion combines results (RRF)
   ↓
5. Cross-encoder reranks top results
   ↓
6. LLM Service generates answer
   ├─ Loads conversation memory
   ├─ Formats context from results
   └─ Calls Groq API
   ↓
7. Cache Service stores result
   ↓
8. Return answer + sources to client
```

## Scalability Considerations

### Current Architecture (Single Server)

**Capacity**:
- ~1000 documents
- ~100 concurrent users
- ~10 queries/second

**Bottlenecks**:
- Single server resources
- In-memory BM25 index
- Local file storage

### Scaling Strategies

#### Horizontal Scaling

```
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
   ┌───┴───────────────┐
   │                   │
┌──▼────┐        ┌─────▼──┐
│ App 1 │        │ App 2  │
└───┬───┘        └────┬───┘
    │                 │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Shared Storage │
    │  & Vector DB    │
    └─────────────────┘
```

**Requirements**:
- Shared vector database (Pinecone) ✓
- Centralized file storage (S3, GCS)
- Distributed cache (Redis)
- Session persistence

#### Vertical Scaling

**Optimizations**:
- Increase server RAM for larger BM25 index
- Add GPU for faster embedding generation
- Increase CPU cores for parallel processing

### Performance Optimizations

1. **Caching**:
   - Query result cache (implemented)
   - Embedding cache for repeated texts
   - Document metadata cache

2. **Async Operations**:
   - Concurrent chunk processing
   - Parallel embedding generation
   - Async file I/O

3. **Batch Processing**:
   - Batch vector upserts (100/batch)
   - Batch embedding generation
   - Batch reranking

4. **Index Optimization**:
   - Pinecone index tuning
   - BM25 index pruning for large corpora

## Security Architecture

### Current Implementation

1. **Input Validation**: Pydantic models
2. **File Type Checking**: Extension whitelist
3. **Size Limits**: 10MB max upload
4. **Error Handling**: No sensitive data in errors

### Production Requirements

1. **Authentication**: API keys or OAuth
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Per-user or per-IP
4. **Encryption**: HTTPS in transit, encryption at rest
5. **Audit Logging**: Track all operations
6. **API Keys**: Secure storage (env vars, secrets manager)

## Monitoring & Observability

### Current Metrics

- Request processing time (X-Process-Time header)
- Cache hit rate (/query/cache-stats)
- Service health (/health)

### Production Monitoring

1. **Application Metrics**:
   - Request rate, latency, errors
   - Cache hit/miss rates
   - Query processing times

2. **Infrastructure Metrics**:
   - CPU, memory, disk usage
   - Network throughput
   - Vector DB performance

3. **Business Metrics**:
   - Documents processed
   - Queries per document
   - User sessions

**Recommended Tools**:
- Prometheus + Grafana
- ELK Stack (logging)
- Sentry (error tracking)

## Deployment Architecture

### Development

```
Local Machine
├── Python venv
├── Local file storage
└── External APIs (Groq, Pinecone)
```

### Production (AWS Example)

```
┌────────────────────────────────────────┐
│            Route 53 (DNS)              │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│        CloudFront (CDN)                │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│   Application Load Balancer (ALB)     │
└────────────────┬───────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼──────┐  ┌──────▼───────┐
│  ECS/Fargate │  │  ECS/Fargate │
│  Container 1 │  │  Container 2 │
└───────┬──────┘  └──────┬───────┘
        │                │
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐              ┌────▼─────┐
│   S3   │              │ Pinecone │
│(Files) │              │(Vectors) │
└────────┘              └──────────┘
```

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Framework | FastAPI | REST API server |
| Language | Python 3.9+ | Application code |
| LLM Framework | LangChain | LLM orchestration |
| Vector DB | Pinecone | Embedding storage |
| LLM Provider | Groq | Fast inference |
| Embeddings | Sentence Transformers | Text→Vector |
| Reranker | Cross-Encoder | Result reranking |
| BM25 | rank-bm25 | Keyword search |
| OCR | Tesseract | Text extraction |
| Document Parsing | PyPDF2, python-docx | File processing |
| Caching | cachetools | Query cache |
| Validation | Pydantic | Data validation |

## Design Patterns

1. **Singleton Pattern**: Services (one instance per service)
2. **Factory Pattern**: Service instantiation
3. **Strategy Pattern**: Different retrieval strategies
4. **Pipeline Pattern**: Document processing flow
5. **Repository Pattern**: Data access abstraction

## Future Enhancements

### Near Term
- [ ] Redis for distributed caching
- [ ] Async background tasks for uploads
- [ ] Streaming responses
- [ ] Query expansion

### Long Term
- [ ] Multi-modal support (images in context)
- [ ] Fine-tuned embeddings
- [ ] Query routing to specialized models
- [ ] Real-time document updates
- [ ] Federated search across multiple indexes

---

This architecture balances simplicity, performance, and production-readiness while maintaining clear separation of concerns and scalability paths.
