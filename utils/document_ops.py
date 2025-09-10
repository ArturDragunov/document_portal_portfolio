from __future__ import annotations
from pathlib import Path
from typing import Iterable, List
from fastapi import UploadFile
from langchain.schema import Document
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import DocumentPortalException
from langchain_community.document_loaders import (
  UnstructuredMarkdownLoader,
  PyPDFLoader,
  Docx2txtLoader,
  TextLoader,
  UnstructuredPowerPointLoader, 
  UnstructuredExcelLoader,
  CSVLoader,
)
from hashlib import md5
from utils.ocr_content_extractor import EmbeddedContentExtractor
def load_documents(paths: Iterable[Path], ocr_extractor: "EmbeddedContentExtractor", enable_ocr: False) -> List[Document]:
# def load_documents(paths: Iterable[Path]) -> List[Document]:
    """Load text + OCR docs, ensuring no duplicates."""
    docs: List[Document] = []
    seen_hashes = set()

    for p in paths:
        ext = p.suffix.lower()

        # ---------- normal loaders ----------
        if ext == ".pdf":
            loader = PyPDFLoader(str(p))
        elif ext == ".docx":
            loader = Docx2txtLoader(str(p))
        elif ext == ".txt":
            loader = TextLoader(str(p), encoding="utf-8")
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(str(p))
        elif ext in (".ppt", ".pptx"):
            loader = UnstructuredPowerPointLoader(str(p))
        elif ext in (".xlsx", ".xls"):
            loader = UnstructuredExcelLoader(str(p))
        elif ext == ".csv":
            loader = CSVLoader(str(p))
        else:
            log.warning("Unsupported extension skipped", path=str(p))
            continue

        try:
            docs.extend(loader.load())
            log.info(f"Text extraction was successful for {p}")
        except Exception as e:
            log.error(f"Failed text extraction from {p}: {e}")
            raise DocumentPortalException("Error loading documents", e) from e
        if enable_ocr:
            # ---------- OCR for embedded images ----------
            try:
                if ext == ".pdf":
                    docs.extend(ocr_extractor.extract_images_from_pdf(str(p)))
                elif ext == ".docx":
                    docs.extend(ocr_extractor.extract_images_from_docx(str(p)))
                elif ext in (".ppt", ".pptx"):
                    docs.extend(ocr_extractor.extract_images_from_pptx(str(p)))
                elif ext in (".png", ".jpg", ".jpeg"):
                    img_doc = ocr_extractor._process_embedded_image(
                    p.read_bytes(),
                    {"source": str(p), "type": "image_file"},
                    )
                    if img_doc:
                        docs.extend(img_doc)   
                log.info(f"Image extraction was successful for {p}")
            except Exception as e:
                log.error(f"OCR extraction failed for {p}: {e}")
        # ---------- Table extraction ----------
        try:
            if ext == ".pdf":
                docs.extend(ocr_extractor.extract_tables_from_pdf(str(p)))
            elif ext == ".docx":
                docs.extend(ocr_extractor.extract_tables_from_docx(str(p)))
            elif ext in (".ppt", ".pptx"):
                docs.extend(ocr_extractor.extract_tables_from_pptx(str(p)))
            log.info(f"Table extraction was successful for {p}")
        except Exception as e:
            log.error(f"OCR extraction failed for {p}: {e}")
    # ---------- Deduplicate ----------
    unique_docs = []
    for d in docs:
        text_hash = md5(d.page_content.strip().encode("utf-8")).hexdigest()
        if text_hash not in seen_hashes:
            unique_docs.append(d)
            seen_hashes.add(text_hash)

    return docs

def concat_for_analysis(docs: List[Document]) -> str:
    parts = []
    for d in docs:
        src = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
        parts.append(f"\n--- SOURCE: {src} ---\n{d.page_content}")
    return "\n".join(parts)

def concat_for_comparison(ref_docs: List[Document], act_docs: List[Document]) -> str:
    left = concat_for_analysis(ref_docs)
    right = concat_for_analysis(act_docs)
    return f"<<REFERENCE_DOCUMENTS>>\n{left}\n\n<<ACTUAL_DOCUMENTS>>\n{right}"

# ---------- Helpers ----------
class FastAPIFileAdapter:
    """Adapt FastAPI UploadFile -> .name + .getbuffer() API"""
    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename
    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()

def read_pdf_via_handler(handler, path: str) -> str:
    if hasattr(handler, "read_pdf"):
        return handler.read_pdf(path)  # type: ignore
    if hasattr(handler, "read_"):
        return handler.read_(path)  # type: ignore
    raise RuntimeError("DocHandler has neither read_pdf nor read_ method.")