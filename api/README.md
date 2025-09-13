# FastAPI Document Portal - Beginner's Guide

This is a web API built with FastAPI for document analysis and comparison. Here's what each part does:

## 1. Basic Setup & Imports

```python
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
app = FastAPI(title="Documnet Portal API", version="0.1")
```

- Creates the main FastAPI application instance
- Sets a title and version for your API
- FastAPI automatically generates interactive documentation at `/docs`

## 2. CORS Middleware (Cross-Origin Requests)

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

**Why this matters:** Browsers block requests between different domains by default. This middleware allows your frontend (running on one port) to talk to your API (running on another port).

- `allow_origins=["*"]` - Any website can call your API
- `allow_credentials=True` - Allows cookies/authentication
- `allow_methods/headers=["*"]` - Allows all HTTP methods and headers

⚠️ **Security Note:** `["*"]` is very permissive - fine for development, restrict in production.

## 3. Static Files & Templates

```python
app.mount("/static", StaticFiles(directory="../static"), name="static")
templates = Jinja2Templates(directory="../templates")
```

- **Static files:** CSS, JS, images served from `/static` URL
- **Templates:** HTML files that can include dynamic data (like variables)

## 4. API Endpoints (Routes)

### Root Endpoint - Serves Web UI
```python
@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```
- When someone visits your website root, it shows `index.html`
- This makes your API also serve a web interface

### Health Check
```python
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "document-portal"}
```
- Simple endpoint to check if your API is running
- Returns JSON: `{"status": "ok", "service": "document-portal"}`

### File Upload Endpoints
```python
@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Any:
```

**Key FastAPI concepts:**
- `@app.post()` - Handles POST requests (for sending data)
- `UploadFile = File(...)` - Accepts file uploads
- `async def` - Handles requests asynchronously (good for I/O operations)
- `HTTPException` - Returns proper error responses

### The Four Main Features:

1. **`/analyze`** - Upload single document for analysis
2. **`/compare`** - Upload two files (reference vs actual) for comparison
3. **`/chat/index`** - Build search index for chat functionality
4. **`/chat/query`** - Query the indexed documents

## 5. Error Handling Pattern

Each endpoint follows this pattern:
```python
try:
    pass  # Your actual logic goes here
except HTTPException:
    raise  # Re-raise HTTP errors as-is
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
```

- Catches any unexpected errors
- Returns proper HTTP 500 (Internal Server Error) responses
- Includes error message for debugging

## 6. Running the Application

```bash
uvicorn api.main:app --reload
```

- `api.main:app` - Points to the `app` variable in `api/main.py`
- `--reload` - Automatically restarts when you change code
- Default runs on `http://localhost:8000`

## 7. What You'll See

- **API Docs:** Visit `http://localhost:8000/docs` for interactive API documentation
- **Web UI:** Visit `http://localhost:8000` to see your HTML interface
- **Health Check:** Visit `http://localhost:8000/health` to test if it's working