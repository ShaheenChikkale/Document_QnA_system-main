# API Documentation

## Overview

The Document Q&A System provides a RESTful API for document management and intelligent question answering with advanced retrieval capabilities.

**Base URL:** `http://localhost:8000`

**API Documentation:** 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication

Currently, the API does not require authentication. For production use, implement API key or OAuth authentication.

## Common Headers

```
Content-Type: application/json
Accept: application/json
```

## Response Format

All responses follow a consistent structure:

**Success Response:**
```json
{
  "data": { ... },
  "status": "success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Error Response:**
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Rate Limiting

No rate limiting is currently implemented. Consider adding rate limiting for production use.

## Endpoints

### 1. Document Management

#### 1.1 Upload Document

Upload and index a document for Q&A.

**Endpoint:** `POST /documents/upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (file, required): Document file (PDF, DOCX, TXT, PNG, JPG, JPEG)

**Request Example:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "document_id": "abc123-def456-ghi789",
  "filename": "document.pdf",
  "file_size": 1024000,
  "pages": 10,
  "chunks_created": 45,
  "status": "success",
  "message": "Document successfully uploaded and indexed with 45 chunks",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `201`: Document uploaded successfully
- `400`: Invalid file type or corrupted file
- `413`: File too large
- `500`: Server error

---

#### 1.2 List Documents

Retrieve all uploaded documents with metadata.

**Endpoint:** `GET /documents`

**Request Example:**
```bash
curl http://localhost:8000/documents
```

**Response:**
```json
{
  "documents": [
    {
      "document_id": "abc123-def456-ghi789",
      "filename": "document.pdf",
      "file_size": 1024000,
      "upload_date": "2024-01-01T00:00:00Z",
      "pages": 10,
      "chunks_count": 45,
      "language": "en"
    }
  ],
  "total_count": 1
}
```

**Status Codes:**
- `200`: Success
- `500`: Server error

---

#### 1.3 Get Document Details

Retrieve metadata for a specific document.

**Endpoint:** `GET /documents/{document_id}`

**Path Parameters:**
- `document_id` (string, required): Document identifier

**Request Example:**
```bash
curl http://localhost:8000/documents/abc123-def456-ghi789
```

**Response:**
```json
{
  "document_id": "abc123-def456-ghi789",
  "filename": "document.pdf",
  "file_size": 1024000,
  "upload_date": "2024-01-01T00:00:00Z",
  "pages": 10,
  "chunks_count": 45,
  "language": "en"
}
```

**Status Codes:**
- `200`: Success
- `404`: Document not found
- `500`: Server error

---

#### 1.4 Delete Document

Remove a document and all its data from the system.

**Endpoint:** `DELETE /documents/{document_id}`

**Path Parameters:**
- `document_id` (string, required): Document identifier

**Request Example:**
```bash
curl -X DELETE http://localhost:8000/documents/abc123-def456-ghi789
```

**Response:**
```json
{
  "document_id": "abc123-def456-ghi789",
  "status": "success",
  "message": "Document document.pdf successfully deleted",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `200`: Success
- `404`: Document not found
- `500`: Server error

---

### 2. Query & Conversation

#### 2.1 Query Documents

Ask questions about uploaded documents with conversational memory.

**Endpoint:** `POST /query`

**Request Body:**
```json
{
  "question": "What is the main topic of the document?",
  "session_id": "optional-session-id",
  "top_k": 5,
  "include_sources": true
}
```

**Parameters:**
- `question` (string, required, 1-1000 chars): The question to ask
- `session_id` (string, optional): Session ID for conversation continuity
- `top_k` (integer, optional, 1-10, default: 5): Number of results to return
- `include_sources` (boolean, optional, default: true): Include source documents

**Request Example:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic?",
    "top_k": 5,
    "include_sources": true
  }'
```

**Response:**
```json
{
  "answer": "Based on the documents, the main topic is...",
  "sources": [
    {
      "document_id": "abc123-def456-ghi789",
      "filename": "document.pdf",
      "page": 3,
      "chunk_id": "abc123_chunk_5",
      "relevance_score": 0.92,
      "content": "The relevant excerpt from the document..."
    }
  ],
  "session_id": "generated-or-provided-session-id",
  "confidence_score": null,
  "processing_time": 1.234,
  "cached": false,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid request (empty question, etc.)
- `500`: Server error

---

#### 2.2 Clear Conversation Memory

Reset conversation history for a session or all sessions.

**Endpoint:** `POST /query/clear-memory`

**Query Parameters:**
- `session_id` (string, optional): Session ID to clear. If not provided, clears all sessions.

**Request Example:**
```bash
# Clear specific session
curl -X POST "http://localhost:8000/query/clear-memory?session_id=abc123"

# Clear all sessions
curl -X POST "http://localhost:8000/query/clear-memory"
```

**Response:**
```json
{
  "session_id": "abc123",
  "status": "success",
  "message": "Conversation memory cleared for session abc123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `200`: Success
- `500`: Server error

---

#### 2.3 Get Conversation History

Retrieve conversation history for a session.

**Endpoint:** `GET /query/history/{session_id}`

**Path Parameters:**
- `session_id` (string, required): Session identifier

**Request Example:**
```bash
curl http://localhost:8000/query/history/abc123
```

**Response:**
```json
{
  "session_id": "abc123",
  "history": [
    {
      "role": "user",
      "content": "What is the main topic?"
    },
    {
      "role": "assistant",
      "content": "The main topic is..."
    },
    {
      "role": "user",
      "content": "Can you elaborate?"
    },
    {
      "role": "assistant",
      "content": "Certainly, ..."
    }
  ],
  "turn_count": 4
}
```

**Status Codes:**
- `200`: Success
- `500`: Server error

---

#### 2.4 Cache Statistics

Retrieve cache performance metrics.

**Endpoint:** `GET /query/cache-stats`

**Request Example:**
```bash
curl http://localhost:8000/query/cache-stats
```

**Response:**
```json
{
  "cache_statistics": {
    "cache_size": 45,
    "max_size": 100,
    "hit_count": 28,
    "miss_count": 17,
    "hit_rate": 0.622
  },
  "description": "Cache performance metrics"
}
```

**Status Codes:**
- `200`: Success
- `500`: Server error

---

### 3. System

#### 3.1 Health Check

Check system health and service status.

**Endpoint:** `GET /health`

**Request Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "embedding_service": "healthy",
    "vector_database": "healthy",
    "llm_service": "healthy",
    "cache_service": "healthy"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `200`: System healthy
- `503`: System unhealthy

---

#### 3.2 Root

API information and available endpoints.

**Endpoint:** `GET /`

**Request Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Document Q&A System API",
  "version": "1.0.0",
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
```

---

## Example Workflows

### Workflow 1: Upload and Query

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Upload document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    upload_response = requests.post(
        f"{BASE_URL}/documents/upload",
        files=files
    )
    document_id = upload_response.json()["document_id"]

# 2. Query document
query_data = {
    "question": "What are the key findings?",
    "top_k": 5,
    "include_sources": True
}
query_response = requests.post(
    f"{BASE_URL}/query",
    json=query_data
)
print(query_response.json()["answer"])
```

### Workflow 2: Conversational Q&A

```python
import requests

BASE_URL = "http://localhost:8000"

# Initial query
response1 = requests.post(
    f"{BASE_URL}/query",
    json={"question": "What is the document about?"}
)
session_id = response1.json()["session_id"]

# Follow-up question (maintains context)
response2 = requests.post(
    f"{BASE_URL}/query",
    json={
        "question": "Can you elaborate on that?",
        "session_id": session_id
    }
)
print(response2.json()["answer"])
```

### Workflow 3: Document Management

```python
import requests

BASE_URL = "http://localhost:8000"

# List all documents
docs_response = requests.get(f"{BASE_URL}/documents")
documents = docs_response.json()["documents"]

# Delete a document
document_id = documents[0]["document_id"]
delete_response = requests.delete(
    f"{BASE_URL}/documents/{document_id}"
)
print(delete_response.json()["message"])
```

---

## Error Handling

The API uses standard HTTP status codes:

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (invalid input) |
| 404 | Resource not found |
| 413 | Payload too large |
| 500 | Internal server error |
| 503 | Service unavailable |

**Error Response Format:**
```json
{
  "error": "Error Type",
  "detail": "Detailed error message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Best Practices

1. **Session Management**: Reuse session IDs for conversational queries
2. **Caching**: Identical queries are cached for faster responses
3. **Source Filtering**: Use `include_sources: false` when only answer is needed
4. **File Size**: Keep uploads under 10MB for optimal performance
5. **Batch Operations**: Upload multiple documents separately for better tracking
6. **Error Handling**: Always check response status codes
7. **Conversation History**: Clear memory when starting new topics

---

## Performance Tips

- Cache hit rate improves with repeated similar queries
- Reduce `top_k` for faster responses (3-5 recommended)
- Use session IDs to maintain conversation context
- Monitor cache statistics for optimization opportunities

---

## Support

For detailed interactive documentation, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
