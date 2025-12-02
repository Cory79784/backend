# GeoGLI Chatbot API

A standalone API service for the UNCCD GeoGLI Chatbot, designed to be used as a blackbox component in Dify workflows.

## 🎯 Purpose

This API provides intelligent question-answering capabilities about global land indicators, country profiles, and environmental commitments. It uses BM25 search with intent recognition to deliver fast, accurate responses.

## 📋 Features

- **Intent Recognition**: Automatically detects query intent (country profiles, legislation, commitments)
- **BM25 Search**: Fast keyword-based search across structured data
- **Dify Integration**: Standard HTTP endpoints compatible with Dify workflows
- **Session Management**: Maintains conversation context
- **Health Monitoring**: Built-in health check endpoints

## 🏗️ Project Structure

```
API/
├── backend/
│   ├── app/
│   │   ├── main.py              # Main FastAPI application
│   │   ├── routes/
│   │   │   ├── dify.py          # Dify-compatible endpoints
│   │   │   └── export.py        # Data export endpoints
│   │   ├── search/
│   │   │   ├── bm25_store.py    # BM25 search engine
│   │   │   ├── router_intent.py # Intent recognition
│   │   │   └── handlers.py      # Query handlers
│   │   ├── schemas.py           # Pydantic models
│   │   └── database.py          # Session storage
│   ├── corpus/
│   │   ├── combined_tables.jsonl       # Main data corpus
│   │   └── combined_tables_hits.jsonl  # Indexed hits
│   ├── data/
│   │   ├── combined_tables.jsonl       # BM25 indexed data
│   │   ├── combined_tables_hits.jsonl  # BM25 hits data
│   │   ├── citations/                  # Citation files
│   │   └── snapshots/                  # Visualization snapshots
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Docker configuration
│   └── .env                    # Environment variables
├── render.yaml                 # Render deployment config
├── test-api.py                 # API test script
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend/` directory:

```env
# BM25 Search Configuration
RAG_BM25_ENABLED=true
BM25_TOP_K=3

# Dense RAG (disabled for this API)
RAG_DENSE_ENABLED=false

# CORS Configuration
ALLOWED_ORIGINS=*

# Database
DATABASE_URL=sqlite:///./chatbot.db
```

### 3. Run the Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 4. Test the API

```bash
# From the API directory
python test-api.py
```

## 📡 API Endpoints

### Core Dify Endpoints

#### 1. **POST /api/dify/chat**
Main chat endpoint for Dify workflows.

**Request:**
```json
{
  "query": "What are the drought trends in Saudi Arabia?",
  "conversation_id": "optional-session-id",
  "user": "optional-user-id"
}
```

**Response:**
```json
{
  "event": "message",
  "message_id": "msg_1234567890",
  "conversation_id": "session-abc-123",
  "mode": "chat",
  "answer": "**Drought Trends in Saudi Arabia**\n\nBased on available data...",
  "metadata": {
    "intent": "ask.country",
    "hits": [...],
    "latency_ms": 45,
    "source": "bm25"
  },
  "created_at": 1234567890
}
```

#### 2. **POST /api/dify/recognize**
Intent recognition and entity extraction.

**Request:**
```json
{
  "query": "Saudi Arabia wildfires"
}
```

**Response:**
```json
{
  "targets": ["saudi arabia"],
  "domain": "country_profile",
  "section_hint": "stressors/fires",
  "iso3_codes": ["SAU"],
  "query": "Saudi Arabia wildfires"
}
```

#### 3. **GET /api/dify/health**
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "GeoGLI-Chatbot-Dify",
  "version": "1.0.0",
  "bm25_enabled": true
}
```

### Additional Endpoints

#### **GET /health**
General health check.

#### **GET /query** or **POST /query**
Direct query endpoint (alternative to Dify endpoint).

**Parameters:**
- `q`: Query string
- `session_id`: Optional session ID
- `route_hint`: Optional routing hint (A, B, or auto)

#### **GET /debug/bm25**
Debug endpoint to test BM25 search.

**Parameters:**
- `q`: Query string

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAG_BM25_ENABLED` | `true` | Enable BM25 search |
| `BM25_TOP_K` | `3` | Number of top results to return |
| `RAG_DENSE_ENABLED` | `false` | Enable dense vector search (not used) |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |
| `DATABASE_URL` | `sqlite:///./chatbot.db` | Database connection string |

## 🐳 Docker Deployment

### Build and Run

```bash
cd backend
docker build -t geoglichatbot-api .
docker run -p 8000:8000 geoglichatbot-api
```

## ☁️ Cloud Deployment (Render)

This API is configured for one-click deployment to Render.

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy to Render**
   - Visit https://render.com
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to deploy

3. **Access Your API**
   - Your API will be available at: `https://YOUR_APP_NAME.onrender.com`
   - Health check: `https://YOUR_APP_NAME.onrender.com/api/dify/health`

## 🧪 Testing

### Run Test Suite

```bash
python test-api.py
```

This will test:
- ✅ Health check endpoints
- ✅ Chat endpoint with various queries
- ✅ Intent recognition
- ✅ Session management
- ✅ Error handling

### Manual Testing with cURL

```bash
# Health check
curl http://localhost:8000/api/dify/health

# Chat query
curl -X POST http://localhost:8000/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are drought trends in Kenya?"}'

# Intent recognition
curl -X POST http://localhost:8000/api/dify/recognize \
  -H "Content-Type: application/json" \
  -d '{"query": "Saudi Arabia wildfires"}'
```

## 🔗 Using in Dify

### HTTP Request Node Configuration

1. **Add HTTP Request Node** in your Dify workflow

2. **Configure the node:**
   - **URL**: `https://your-api-url.onrender.com/api/dify/chat`
   - **Method**: `POST`
   - **Headers**: `Content-Type: application/json`
   - **Body**:
     ```json
     {
       "query": "{{input.user_query}}",
       "conversation_id": "{{conversation_id}}"
     }
     ```

3. **Use the response:**
   - Answer: `{{http_request.data.answer}}`
   - Intent: `{{http_request.data.metadata.intent}}`
   - Hits: `{{http_request.data.metadata.hits}}`

### Example Workflow

```
User Input → HTTP Request (recognize) → Conditional Logic → HTTP Request (chat) → Output
```

## 📊 Data Structure

### Corpus Files

The API uses two main data files in `backend/corpus/` and `backend/data/`:

- **combined_tables.jsonl**: Main data corpus with country profiles, indicators, and commitments
- **combined_tables_hits.jsonl**: Indexed hits for fast BM25 retrieval

Each line is a JSON object with:
```json
{
  "id": "unique-id",
  "country": "Country Name",
  "iso3": "ISO",
  "section": "section/subsection",
  "title": "Title",
  "text": "Content text",
  "images": ["path/to/image.png"],
  "citation_path": "path/to/citation.md"
}
```

## 🛠️ Development

### Adding New Intents

1. Edit `backend/app/search/router_intent.py`
2. Add new intent patterns
3. Create handler in `backend/app/search/handlers.py`
4. Update domain mapping in `backend/app/routes/dify.py`

### Updating Data

1. Replace files in `backend/corpus/` and `backend/data/`
2. Restart the server to rebuild BM25 indices

## 📝 License

This project is part of the UNCCD GeoGLI initiative.

## 🤝 Support

For issues or questions:
- Check the health endpoint: `/api/dify/health`
- Review logs for error messages
- Test with the debug endpoint: `/debug/bm25?q=your+query`

## 🔄 Version History

- **1.0.0** (2024-11): Initial release with BM25 search and Dify integration
