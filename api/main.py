import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.document_ingestion.data_ingestion import (
    DocHandler,
    DocumentComparator,
    ChatIngestor,
)
from src.document_analyzer.data_analysis import DocumentAnalyzer
from src.document_compare.document_comparator import DocumentComparatorLLM
from src.document_chat.retrieval import ConversationalRAG
from utils.document_ops import FastAPIFileAdapter,read_pdf_via_handler
from logger import GLOBAL_LOGGER as log

from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache

# base dir = project root (two levels up from api/main.py)
BASE_DIR = Path(__file__).resolve().parent.parent
# point to data folder inside project root
CACHE_DB_PATH = BASE_DIR / "data" / "llm_cache.db"
# set global persistent cache
set_llm_cache(SQLiteCache(database_path=str(CACHE_DB_PATH)))

FAISS_BASE = os.getenv("FAISS_BASE", "faiss_index")
UPLOAD_BASE = os.getenv("UPLOAD_BASE", "data")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")  # <--- keep consistent with save_local()

app = FastAPI(title="Document Portal API", version="0.1")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# home page of our application is index.html. We are rendering it upon request.
@app.get("/", response_class=HTMLResponse) # "/" defines the root URL. You visit it and you see index.html
async def serve_ui(request: Request):
    log.info("Serving UI homepage.")
    resp = templates.TemplateResponse(request, "index.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.get("/health") # e.g. http://127.0.0.1:8080/health will give you health logs
def health() -> Dict[str, str]:
    log.info("Health check passed.")
    return {"status": "ok", "service": "document-portal"}

# ---------- ANALYZE ----------
@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)) -> Any:
    try:
        log.info(f"Received file for analysis: {file.filename}")
        dh = DocHandler()
        # We need FastAPIFileAdapter to reformat file for our save_pdf needs. 
        saved_path = dh.save_pdf(FastAPIFileAdapter(file))
        text = read_pdf_via_handler(dh, saved_path)
        analyzer = DocumentAnalyzer()
        result = analyzer.analyze_document(text)
        log.info("Document analysis complete.")
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Error during document analysis")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

# ---------- COMPARE ----------
@app.post("/compare") # two files are allowed to be uploaded
async def compare_documents(reference: UploadFile = File(...), actual: UploadFile = File(...)) -> Any:
    try:
        log.info(f"Comparing files: {reference.filename} vs {actual.filename}")
        dc = DocumentComparator()
        _, _  = dc.save_uploaded_files( # we save copies of files under session
            FastAPIFileAdapter(reference), FastAPIFileAdapter(actual)
        )
        # _ = ref_path, act_path
        combined_text = dc.combine_documents()
        comp = DocumentComparatorLLM()
        df = comp.compare_documents(combined_text)
        log.info("Document comparison completed.")
        return {"rows": df.to_dict(orient="records"), "session_id": dc.session_id}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Comparison failed")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")

# ---------- CHAT: INDEX ----------
@app.post("/chat/index")
async def chat_build_index(
    files: List[UploadFile] = File(...), # many files can be uploaded!
    session_id: Optional[str] = Form(None),
    # if session is true, we will build a new session in faiss_index and save pickle and index there
    #Otherwise, we save pickle and index to a root location
    use_session_dirs: bool = Form(True),
    k: int = Form(5),
    enable_ocr: bool = Form(False)
) -> Any:
    try:
        log.info(f"Indexing chat session. Session ID: {session_id}, Files: {[f.filename for f in files]}")
        wrapped = [FastAPIFileAdapter(f) for f in files]
        # this is my main class for storing a data into VDB
        # created a object of ChatIngestor
        ci = ChatIngestor(
            temp_base=UPLOAD_BASE,
            faiss_base=FAISS_BASE,
            use_session_dirs=use_session_dirs,
            session_id=session_id or None,
        )
        # NOTE: ensure your ChatIngestor saves with index_name="index" or FAISS_INDEX_NAME
        # e.g., if it calls FAISS.save_local(dir, index_name=FAISS_INDEX_NAME)
        ci.build_retriever(  # if your method name is actually build_retriever, fix it there as well
            wrapped, k=k, enable_ocr=enable_ocr
        ) # these values are provided by a user in UI
        log.info(f"Index created successfully for session: {ci.session_id}")
        return {"session_id": ci.session_id, "k": k, "use_session_dirs": use_session_dirs}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Chat index building failed")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

# ---------- CHAT: QUERY ----------
@app.post("/chat/query")
async def chat_query(
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool = Form(True),
    k: int = Form(5),
) -> Any:
    try:
        log.info(f"Received chat query: '{question}' | session: {session_id}")
        if use_session_dirs and not session_id:
            raise HTTPException(status_code=400, detail="session_id is required when use_session_dirs=True")

        index_dir = os.path.join(FAISS_BASE, session_id) if use_session_dirs else FAISS_BASE  # type: ignore
        if not os.path.isdir(index_dir):
            raise HTTPException(status_code=404, detail=f"FAISS index not found at: {index_dir}")

        rag = ConversationalRAG(session_id=session_id)
        rag.load_retriever_from_faiss(index_dir, k=k, index_name=FAISS_INDEX_NAME)  # build retriever + chain
        response = rag.invoke(question, chat_history=[])
        log.info("Chat query handled successfully.")

        return {
            "answer": response,
            "session_id": session_id,
            "k": k,
            "engine": "LCEL-RAG"
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Chat query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

# command for executing the fast api
# uvicorn api.main:app --port 8080 --reload    
#uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload