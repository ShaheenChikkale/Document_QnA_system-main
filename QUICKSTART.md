# Quick Start Guide

Get your Document Q&A System running in 5 minutes!

## Prerequisites

- Python 3.9+
- Tesseract OCR
- API Keys (Groq & Pinecone)

## Installation Steps

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

### 2. Clone and Setup

```bash
# Clone repository
cd document-qa-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your keys
nano .env  # or use any text editor
```

Required keys:
```env
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

**Get API Keys:**
- Groq: https://console.groq.com (Free tier available)
- Pinecone: https://www.pinecone.io (Free tier available)

### 4. Start the Server

```bash
python -m app.main
```

Or:
```bash
uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

### 5. Test the API

**Open API Docs:**
Visit: `http://localhost:8000/docs`

**Test with cURL:**
```bash
# Health check
curl http://localhost:8000/health

# Upload a document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@your_document.pdf"

# Ask a question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

## Alternative: Docker Setup

```bash
# Copy .env file
cp .env.example .env
# Edit with your API keys

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Running Tests

```bash
# Run comprehensive test suite
python test_suite.py path/to/test/document.pdf
```

## Common Issues

**Issue: Tesseract not found**
```bash
# Install Tesseract
sudo apt-get install tesseract-ocr  # Linux
brew install tesseract              # macOS
```

**Issue: Pinecone connection error**
- Verify API key in `.env`
- Check index name matches

**Issue: Out of memory**
- Reduce `CHUNK_SIZE` in `.env` to 300
- Reduce `TOP_K_RETRIEVAL` to 5

## Next Steps

1. **Upload Documents**: Use `/docs` interface or cURL
2. **Ask Questions**: POST to `/query` endpoint
3. **Explore Features**: Try conversational queries
4. **Monitor Performance**: Check `/query/cache-stats`

## Features to Try

### 1. Basic Q&A
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Summarize the main points",
    "top_k": 5
  }'
```

### 2. Conversational Follow-up
```bash
# First query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the document about?"}'
  
# Save the session_id from response

# Follow-up query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tell me more about that",
    "session_id": "YOUR_SESSION_ID"
  }'
```

### 3. Multilingual Documents
- Upload documents in any language
- System automatically detects language
- Ask questions in English (or document language)

### 4. Scanned Documents
- Upload scanned PDFs or images
- OCR automatically extracts text
- Query as normal

## Documentation

- **Full README**: `README.md`
- **API Reference**: `API_DOCUMENTATION.md`
- **Interactive Docs**: `http://localhost:8000/docs`

## Support

- Check logs for errors
- Review troubleshooting in README
- Test with provided test suite

## Performance Tips

- **Faster responses**: Reduce `top_k` to 3
- **Better accuracy**: Increase `TOP_K_RETRIEVAL` to 15
- **Memory optimization**: Reduce `CHUNK_SIZE` to 400
- **Cache benefits**: Ask similar questions multiple times

Enjoy your production-grade Document Q&A System! 🚀
