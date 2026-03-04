# Document-Based Q&A System

An intelligent Document Q&A system with advanced retrieval capabilities, built using FastAPI, LangChain, Groq API, and Pinecone.

## 🎨 **NEW: Beautiful Web UI!**

**No coding required!** Just upload documents and ask questions through an intuitive web interface.

```
Start server → Open http://localhost:8000/ui → Drag & Drop → Ask Questions!
```

**Features:**
- 📤 Drag & drop document upload
- 💬 Real-time chat interface  
- 📚 Document management panel
- ⚙️ Customizable settings
- 📊 Source citations & processing metrics
- 🎨 Beautiful, responsive design

See [UI_GUIDE.md](UI_GUIDE.md) for complete instructions.

---

## 🌟 Features

### Core Capabilities
- **Hybrid Search**: Combines vector similarity (semantic) and BM25 (keyword) search for optimal retrieval
- **Cross-Encoder Reranking**: Improves result relevance using transformer-based reranking
- **Conversational Memory**: Maintains context across multiple queries for natural follow-up questions
- **Query Caching**: LRU cache for frequently asked questions to improve response time
- **Multilingual Support**: Process and query documents in multiple languages
- **OCR Support**: Extract text from scanned PDFs and images
- **Source Attribution**: Cite specific documents, pages, and chunks in responses

### Advanced Features
- Smart document chunking with overlap for context preservation
- Semantic search with multilingual embeddings
- Contextual answer generation using Groq's fast LLM inference
- REST API with comprehensive documentation
- Production-ready error handling and validation
- Async operations for better performance

## 📋 Table of Contents
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│          FastAPI Application                │
├─────────────────────────────────────────────┤
│  Routes: /documents, /query, /health        │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│            Services Layer                   │
├──────────────┬──────────────┬───────────────┤
│  Document    │  Embedding   │   Retrieval   │
│  Processor   │   Service    │   Service     │
├──────────────┼──────────────┼───────────────┤
│  LLM Service │ Cache Service│               │
└──────┬───────┴──────┬───────┴───────┬───────┘
       │              │               │
┌──────▼──────┐  ┌───▼────┐   ┌──────▼──────┐
│  Pinecone   │  │ Groq   │   │ Local Cache │
│   (Vector)  │  │ (LLM)  │   │    (LRU)    │
└─────────────┘  └────────┘   └─────────────┘
```

### Component Breakdown

1. **Document Processor**
   - Handles file uploads (PDF, DOCX, TXT, images)
   - Applies OCR for scanned documents
   - Smart text chunking with overlap
   - Language detection

2. **Embedding Service**
   - Generates multilingual vector embeddings
   - Manages Pinecone vector database
   - Handles document indexing and deletion

3. **Retrieval Service**
   - Hybrid search (Vector + BM25)
   - Cross-encoder reranking
   - Context optimization

4. **LLM Service**
   - Groq API integration with LangChain
   - Conversational memory management
   - RAG (Retrieval-Augmented Generation)
   - Source citation generation

5. **Cache Service**
   - LRU caching for query results
   - Cache invalidation on document updates
   - Performance metrics

## 🚀 Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR (for scanned documents)
- API Keys:
  - [Groq API Key](https://console.groq.com)
  - [Pinecone API Key](https://www.pinecone.io)

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

**Windows:**
- Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Download and install [Poppler](http://blog.alivate.com.au/poppler-windows/)

### Python Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd document-qa-system
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=document-qa-index
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (required) | - |
| `PINECONE_API_KEY` | Pinecone API key (required) | - |
| `PINECONE_INDEX_NAME` | Pinecone index name | document-qa-index |
| `EMBEDDING_MODEL` | Sentence transformer model | paraphrase-multilingual-mpnet-base-v2 |
| `RERANKER_MODEL` | Cross-encoder model | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| `LLM_MODEL` | Groq model name | mixtral-8x7b-32768 |
| `CHUNK_SIZE` | Text chunk size | 500 |
| `CHUNK_OVERLAP` | Chunk overlap | 100 |
| `TOP_K_RETRIEVAL` | Initial retrieval count | 10 |
| `TOP_K_RERANK` | Final reranked results | 5 |
| `CACHE_SIZE` | LRU cache size | 100 |
| `MAX_FILE_SIZE` | Max upload size (bytes) | 10485760 (10MB) |

### Model Selection

**Groq Models (Fast Inference):**
- `mixtral-8x7b-32768` (Recommended - Balanced)
- `llama3-70b-8192` (High Quality)
- `llama3-8b-8192` (Fast)
- `gemma-7b-it` (Lightweight)

## 📖 Usage

### Starting the Server

```bash
# Development mode with auto-reload
python -m app.main

# OR using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Basic Workflow

#### 1. Upload Documents
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf"
```

**Response:**
```json
{
  "document_id": "abc123...",
  "filename": "document.pdf",
  "file_size": 1024000,
  "pages": 10,
  "chunks_created": 45,
  "status": "success",
  "message": "Document successfully uploaded and indexed with 45 chunks"
}
```

#### 2. Ask Questions
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key findings in the document?",
    "top_k": 5,
    "include_sources": true
  }'
```

**Response:**
```json
{
  "answer": "Based on the documents, the key findings are...",
  "sources": [
    {
      "document_id": "abc123...",
      "filename": "document.pdf",
      "page": 3,
      "chunk_id": "abc123_chunk_5",
      "relevance_score": 0.92,
      "content": "..."
    }
  ],
  "session_id": "session-xyz",
  "processing_time": 1.234,
  "cached": false
}
```

#### 3. Follow-up Questions (Conversational)
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you elaborate on the second finding?",
    "session_id": "session-xyz",
    "top_k": 3
  }'
```

## 🔌 API Endpoints

### Document Management

#### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <file>
```
Uploads and indexes a document. Supports PDF, DOCX, TXT, PNG, JPG, JPEG.

#### List Documents
```http
GET /documents
```
Returns list of all uploaded documents with metadata.

#### Get Document Details
```http
GET /documents/{document_id}
```
Retrieves metadata for a specific document.

#### Delete Document
```http
DELETE /documents/{document_id}
```
Removes a document and all its chunks from the system.

### Query & Conversation

#### Query Documents
```http
POST /query
Content-Type: application/json

{
  "question": "string",
  "session_id": "string (optional)",
  "top_k": 5,
  "include_sources": true
}
```
Queries the knowledge base with conversational memory support.

#### Clear Conversation Memory
```http
POST /query/clear-memory?session_id=<session_id>
```
Resets conversation history for a session.

#### Get Conversation History
```http
GET /query/history/{session_id}
```
Retrieves conversation history for a session.

#### Cache Statistics
```http
GET /query/cache-stats
```
Returns cache performance metrics.

### System

#### Health Check
```http
GET /health
```
Returns system health status.

#### Root
```http
GET /
```
API information and feature list.

## 🧪 Testing

### Manual Testing Script

Create `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Upload a document
def test_upload():
    with open("test_document.pdf", "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)
        print("Upload Response:", response.json())
        return response.json()["document_id"]

# 2. Query the document
def test_query(session_id=None):
    data = {
        "question": "What is the main topic of the document?",
        "session_id": session_id,
        "top_k": 5,
        "include_sources": True
    }
    response = requests.post(f"{BASE_URL}/query", json=data)
    result = response.json()
    print("\nQuery Response:")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {len(result['sources'])}")
    print(f"Processing Time: {result['processing_time']:.3f}s")
    return result["session_id"]

# 3. Follow-up question
def test_followup(session_id):
    data = {
        "question": "Can you provide more details?",
        "session_id": session_id,
        "top_k": 3
    }
    response = requests.post(f"{BASE_URL}/query", json=data)
    result = response.json()
    print("\nFollow-up Response:")
    print(f"Answer: {result['answer']}")
    print(f"Cached: {result['cached']}")

# Run tests
if __name__ == "__main__":
    doc_id = test_upload()
    session_id = test_query()
    test_followup(session_id)
```

Run:
```bash
python test_api.py
```

### Using cURL

**Health Check:**
```bash
curl http://localhost:8000/health
```

**List Documents:**
```bash
curl http://localhost:8000/documents
```

**Cache Stats:**
```bash
curl http://localhost:8000/query/cache-stats
```

## 🔥 Advanced Features

### 1. Hybrid Search

The system combines two search methods:
- **Vector Search**: Semantic similarity using embeddings
- **BM25 Search**: Keyword-based ranking

Results are fused using Reciprocal Rank Fusion (RRF) with configurable weights.

### 2. Cross-Encoder Reranking

After initial retrieval, results are reranked using a cross-encoder model that:
- Evaluates query-document pairs jointly
- Provides more accurate relevance scores
- Significantly improves answer quality

### 3. Conversational Memory

The system maintains conversation context:
- Handles follow-up questions naturally
- References previous answers
- Maintains session-based memory
- Configurable history length

### 4. Smart Caching

Query results are cached using LRU strategy:
- Exact query matching
- Automatic invalidation on document updates
- Configurable cache size
- Performance metrics tracking

### 5. Multilingual Support

- Processes documents in 100+ languages
- Automatic language detection
- Multilingual embeddings
- Cross-lingual retrieval

### 6. OCR Integration

Automatically detects and processes scanned documents:
- Extracts text from images
- Handles scanned PDFs
- Multiple language support
- Page-level processing

## 🐛 Troubleshooting

### Common Issues

**1. Tesseract not found**
```
Error: Tesseract is not installed or not in PATH
```
**Solution:** Install Tesseract OCR and ensure it's in your system PATH.

**2. Pinecone connection error**
```
Error: Failed to connect to Pinecone
```
**Solution:** Check your API key and ensure index name is correct.

**3. Out of memory**
```
Error: CUDA out of memory / System memory exceeded
```
**Solution:** Reduce `CHUNK_SIZE` or `TOP_K_RETRIEVAL` in `.env`.

**4. Slow performance**
```
Processing takes too long
```
**Solutions:**
- Enable caching
- Reduce `TOP_K_RETRIEVAL`
- Use smaller embedding model
- Use faster Groq model (llama3-8b-8192)

### Performance Optimization

**For faster responses:**
1. Reduce `TOP_K_RETRIEVAL` to 5-7
2. Enable caching
3. Use smaller embedding model
4. Reduce `CHUNK_SIZE` to 300-400

**For better accuracy:**
1. Increase `TOP_K_RETRIEVAL` to 15-20
2. Increase `CHUNK_OVERLAP` to 150
3. Use larger embedding model
4. Use Mixtral or Llama3-70b

## 📊 System Requirements

**Minimum:**
- 4 CPU cores
- 8GB RAM
- 10GB disk space

**Recommended:**
- 8 CPU cores
- 16GB RAM
- 50GB disk space
- GPU (optional, for faster embedding)

## 🔒 Security Considerations

For production deployment:

1. **API Authentication**: Implement API key or OAuth
2. **Rate Limiting**: Add rate limiting middleware
3. **Input Validation**: Enhanced file type checking
4. **CORS**: Configure appropriate CORS origins
5. **HTTPS**: Use HTTPS in production
6. **Environment Variables**: Use secrets management
7. **File Size Limits**: Enforce appropriate limits

## 📝 License

This project is available for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please follow standard git workflow:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check documentation at `/docs` endpoint
- Review API specification at `/redoc`

## 🎯 Future Enhancements

- [ ] Streaming responses
- [ ] Multi-document comparison
- [ ] Table and chart extraction
- [ ] Citation graph visualization
- [ ] Advanced query expansion
- [ ] Custom embedding fine-tuning
- [ ] Multi-modal support (images in context)
- [ ] Real-time document updates

---

**Built with ❤️ using FastAPI, LangChain, Groq, and Pinecone**
