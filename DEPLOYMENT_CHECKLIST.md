# GeoGLI Chatbot API - Deployment Checklist

## 📋 Pre-Deployment Checklist

### ✅ File Structure Verification

Ensure all required files are present:

```
API/
├── backend/
│   ├── app/
│   │   ├── main.py ✓
│   │   ├── routes/
│   │   │   ├── dify.py ✓
│   │   │   └── export.py ✓
│   │   ├── search/
│   │   │   ├── bm25_store.py ✓
│   │   │   ├── router_intent.py ✓
│   │   │   ├── handlers.py ✓
│   │   │   └── pipeline.py ✓
│   │   ├── schemas.py ✓
│   │   ├── database.py ✓
│   │   └── utils/ ✓
│   ├── corpus/
│   │   ├── combined_tables.jsonl ✓ (CRITICAL)
│   │   └── combined_tables_hits.jsonl ✓ (CRITICAL)
│   ├── data/
│   │   ├── combined_tables.jsonl ✓ (CRITICAL)
│   │   └── combined_tables_hits.jsonl ✓ (CRITICAL)
│   ├── requirements.txt ✓
│   ├── Dockerfile ✓
│   └── .env.example ✓
├── render.yaml ✓
├── test-api.py ✓
├── start-api.bat ✓
├── README.md ✓
└── .gitignore ✓
```

### ✅ Data Files Verification

**CRITICAL**: Ensure corpus data files exist and are not empty:

```bash
# Check file sizes (should be > 400KB each)
ls -lh backend/corpus/combined_tables.jsonl
ls -lh backend/corpus/combined_tables_hits.jsonl
ls -lh backend/data/combined_tables.jsonl
ls -lh backend/data/combined_tables_hits.jsonl
```

Expected sizes:
- `combined_tables.jsonl`: ~450-460 KB
- `combined_tables_hits.jsonl`: ~460-480 KB

### ✅ Configuration Files

1. **`.env.example`** exists in `backend/` directory
2. **`.gitignore`** properly configured:
   - ✅ Excludes `.env`
   - ✅ Excludes `.venv/`
   - ✅ **INCLUDES** `corpus/` directory (data files must be tracked!)
   - ✅ Excludes `*.db` files

3. **`render.yaml`** configured with:
   - ✅ Correct Python version (3.11.0)
   - ✅ BM25 enabled (`RAG_BM25_ENABLED=true`)
   - ✅ Correct health check path (`/api/dify/health`)

## 🧪 Local Testing

### Step 1: Start the API

```bash
# Windows
start-api.bat

# Linux/Mac
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Run Test Suite

```bash
# In a new terminal
python test-api.py
```

### Step 3: Manual Testing

Test each endpoint manually:

#### 1. Health Check
```bash
curl http://localhost:8000/api/dify/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "GeoGLI-Chatbot-Dify",
  "version": "1.0.0",
  "bm25_enabled": true
}
```

#### 2. Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are drought trends in Kenya?"}'
```

Expected response structure:
```json
{
  "event": "message",
  "message_id": "msg_...",
  "conversation_id": "...",
  "mode": "chat",
  "answer": "...",
  "metadata": {
    "intent": "ask.country",
    "hits": [...],
    "latency_ms": 50,
    "source": "bm25"
  },
  "created_at": 1234567890
}
```

#### 3. Recognize Endpoint
```bash
curl -X POST http://localhost:8000/api/dify/recognize \
  -H "Content-Type: application/json" \
  -d '{"query": "Saudi Arabia wildfires"}'
```

Expected response:
```json
{
  "targets": ["saudi arabia"],
  "domain": "country_profile",
  "section_hint": "stressors/fires",
  "iso3_codes": ["SAU"],
  "query": "Saudi Arabia wildfires"
}
```

#### 4. Debug BM25
```bash
curl "http://localhost:8000/debug/bm25?q=Kenya+drought"
```

Expected response:
```json
{
  "query": "Kenya drought",
  "intent": "ask.country",
  "slots": {...},
  "hits_count": 3,
  "hits": [...],
  "available_stores": ["geogli"]
}
```

### ✅ Test Results Checklist

- [ ] All health checks return `200 OK`
- [ ] Chat endpoint returns structured responses
- [ ] BM25 search returns hits (hits_count > 0)
- [ ] Intent recognition extracts correct entities
- [ ] Session IDs are maintained across requests
- [ ] Response times are < 1 second for BM25 queries
- [ ] No errors in server logs

## 🚀 GitHub Deployment

### Step 1: Initialize Git Repository

```bash
cd "D:\10.09 - 副本\GeoGLI-Chatbot\API"
git init
git add .
git commit -m "Initial commit: GeoGLI Chatbot API"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `geoglichatbot-api` (or your choice)
3. Description: "GeoGLI Chatbot API - Standalone service for Dify integration"
4. Visibility: Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### ✅ GitHub Verification

After pushing, verify on GitHub:

- [ ] All files are present (check file count)
- [ ] `backend/corpus/` directory exists with data files
- [ ] `backend/data/` directory exists with data files
- [ ] File sizes match local files
- [ ] `.env` is NOT in the repository (should be ignored)
- [ ] README.md displays correctly

## ☁️ Render Deployment

### Step 1: Connect to Render

1. Go to https://render.com
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Select your repository

### Step 2: Configure Service

Render should auto-detect `render.yaml`. Verify:

- **Name**: `geoglichatbot-backend`
- **Runtime**: Python
- **Region**: Oregon (or your choice)
- **Branch**: main
- **Build Command**: 
  ```bash
  cd backend
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  cd backend
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### Step 3: Environment Variables

Verify these are set (from render.yaml):

- `PYTHON_VERSION`: 3.11.0
- `RAG_BM25_ENABLED`: true
- `BM25_TOP_K`: 3
- `RAG_DENSE_ENABLED`: false
- `ALLOWED_ORIGINS`: *
- `DATABASE_URL`: sqlite:///./chatbot.db

### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for build to complete (5-10 minutes)
3. Check build logs for errors

### ✅ Render Deployment Verification

After deployment completes:

#### 1. Check Health Endpoint
```bash
curl https://YOUR_APP_NAME.onrender.com/api/dify/health
```

Should return:
```json
{
  "status": "ok",
  "service": "GeoGLI-Chatbot-Dify",
  "version": "1.0.0",
  "bm25_enabled": true
}
```

#### 2. Test Chat Endpoint
```bash
curl -X POST https://YOUR_APP_NAME.onrender.com/api/dify/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are drought trends in Kenya?"}'
```

#### 3. Check Logs

In Render dashboard:
- [ ] No error messages in logs
- [ ] BM25 stores initialized successfully
- [ ] Server started on correct port

#### 4. Performance Check

- [ ] Health check responds in < 500ms
- [ ] Chat queries respond in < 2 seconds
- [ ] No timeout errors

## 🔗 Dify Integration Testing

### Step 1: Add HTTP Request Node in Dify

1. Create new workflow in Dify
2. Add "HTTP Request" node
3. Configure:
   - **URL**: `https://YOUR_APP_NAME.onrender.com/api/dify/chat`
   - **Method**: POST
   - **Headers**: `Content-Type: application/json`
   - **Body**:
     ```json
     {
       "query": "{{input.user_query}}"
     }
     ```

### Step 2: Test in Dify

Test queries:
- "What are drought trends in Kenya?"
- "Tell me about Saudi Arabia wildfires"
- "Show me climate hazards in Brazil"

### ✅ Dify Integration Checklist

- [ ] HTTP Request node connects successfully
- [ ] Responses are received within timeout
- [ ] Answer text is properly formatted
- [ ] Metadata is accessible
- [ ] Session IDs are maintained

## 🐛 Troubleshooting

### Common Issues

#### 1. BM25 Stores Not Initialized

**Symptom**: Logs show "Failed to initialize BM25 stores"

**Solution**:
- Verify `backend/corpus/combined_tables.jsonl` exists
- Verify `backend/data/combined_tables.jsonl` exists
- Check file sizes (should be > 400KB)
- Ensure files are valid JSONL format

#### 2. Module Import Errors

**Symptom**: `ModuleNotFoundError` in logs

**Solution**:
- Check `requirements.txt` is complete
- Verify build command runs `pip install -r requirements.txt`
- Check Python version is 3.11+

#### 3. Health Check Fails

**Symptom**: 404 or 500 error on `/api/dify/health`

**Solution**:
- Verify `app/routes/dify.py` is present
- Check router is included in `main.py`
- Review server logs for startup errors

#### 4. Empty Responses

**Symptom**: Chat endpoint returns empty answers

**Solution**:
- Test with `/debug/bm25?q=test+query`
- Verify BM25 stores are loaded
- Check data files contain valid entries

#### 5. Slow Response Times

**Symptom**: Queries take > 5 seconds

**Solution**:
- Check Render plan (free tier may be slow on cold start)
- Verify BM25_TOP_K is set to 3 (not higher)
- Consider upgrading Render plan

## 📊 Post-Deployment Monitoring

### Daily Checks

- [ ] Health endpoint returns 200 OK
- [ ] Response times are acceptable
- [ ] No errors in Render logs

### Weekly Checks

- [ ] Review usage metrics in Render dashboard
- [ ] Check for any failed requests
- [ ] Verify data files are still accessible

### Monthly Checks

- [ ] Update dependencies if needed
- [ ] Review and optimize queries
- [ ] Check for any security updates

## 🎉 Deployment Complete!

Once all checklist items are complete, your API is ready for production use in Dify!

**Your API URLs:**
- Health: `https://YOUR_APP_NAME.onrender.com/api/dify/health`
- Chat: `https://YOUR_APP_NAME.onrender.com/api/dify/chat`
- Recognize: `https://YOUR_APP_NAME.onrender.com/api/dify/recognize`
- Docs: `https://YOUR_APP_NAME.onrender.com/docs`

**Next Steps:**
1. Save your API URL in a safe place
2. Configure Dify workflows to use your API
3. Monitor performance and logs
4. Enjoy your intelligent chatbot! 🚀
