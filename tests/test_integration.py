# tests/test_unit_cases.py

import pytest
from fastapi.testclient import TestClient
from api.main import app
from pathlib import Path
from src.document_ingestion.data_ingestion import ChatIngestor
import os
import json
import tempfile
from unittest.mock import Mock, patch
from io import BytesIO

# Import your modules
from src.document_ingestion.data_ingestion import DocHandler, FaissManager, ChatIngestor
from src.document_analyzer.data_analysis import DocumentAnalyzer
from src.document_compare.document_comparator import DocumentComparatorLLM
from src.document_chat.retrieval import ConversationalRAG

client = TestClient(app)
tmp_path = Path(__file__).resolve().parent

# Sample valid PDF content (minimal PDF structure for testing)
VALID_PDF_CONTENT = b"""%PDF-1.0
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test Document) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000059 00000 n 
0000000102 00000 n 
0000000179 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
262
%%EOF
"""

def test_resolve_dir_creates_session(tmp_path):
    ingestor = ChatIngestor(temp_base=tmp_path, faiss_base=tmp_path, use_session_dirs=True)
    result = ingestor._resolve_dir(tmp_path)
    assert result.exists()
    assert ingestor.session_id in str(result)

# Test fixtures
@pytest.fixture
def mock_pdf_content():
    return VALID_PDF_CONTENT

@pytest.fixture
def mock_uploaded_file(mock_pdf_content):
    file_obj = BytesIO(mock_pdf_content)
    file_obj.name = "test.pdf"
    return file_obj

@pytest.fixture
def mock_fitz_open():
    """Mock fitz.open to return a valid document object."""
    with patch('src.document_ingestion.data_ingestion.fitz.open') as mock_fitz:
        mock_doc = Mock()
        mock_doc.is_encrypted = False
        mock_page = Mock()
        mock_page.get_text.return_value = "PDF content"
        mock_doc.page_count = 1
        mock_doc.load_page.return_value = mock_page
        mock_fitz.return_value.__enter__.return_value = mock_doc
        yield mock_fitz

@pytest.fixture
def mock_pypdf_reader():
    """Mock PyPDF2.PdfReader to return a valid document."""
    with patch('PyPDF2.PdfReader') as mock_reader:
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF content"
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        mock_reader.return_value = mock_doc
        yield mock_reader

@pytest.fixture
def mock_faiss():
    """Mock FAISS operations."""
    with patch('src.document_chat.retrieval.FAISS') as mock_faiss:
        mock_vectorstore = Mock()
        mock_vectorstore.as_retriever.return_value = Mock()
        mock_faiss.load_local.return_value = mock_vectorstore
        mock_faiss.from_texts.return_value = mock_vectorstore
        yield mock_faiss
# INTEGRATION TESTS
def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "document-portal"

@patch('api.main.FastAPIFileAdapter')
@patch('api.main.read_pdf_via_handler')
@patch('api.main.DocumentAnalyzer')
@patch('api.main.DocHandler')
def test_analyze_endpoint(mock_doc_handler, mock_analyzer, mock_read_pdf, mock_adapter, mock_fitz_open):
    """Test document analysis endpoint"""
    # Mock file adapter
    mock_file = Mock()
    mock_file.name = "test.pdf"
    mock_file.read.return_value = VALID_PDF_CONTENT
    mock_adapter.return_value = mock_file

    # Mock DocHandler
    mock_handler_instance = Mock()
    mock_handler_instance.save_pdf.return_value = "data/document_analysis/test_session/test.pdf"
    mock_doc_handler.return_value = mock_handler_instance

    # Mock PDF reading
    mock_read_pdf.return_value = "PDF content"

    # Mock analyzer
    mock_analyzer_instance = Mock()
    mock_analyzer_instance.analyze_document.return_value = {
        "Author": ["Unknown"],
        "DateCreated": "Unknown",
        "Language": "Unknown",
        "LastModifiedDate": "Unknown",
        "Title": "Test Document",
        "Summary": "Test summary",
        "Keywords": [],
        "References": [],
        "Citations": []
    }
    mock_analyzer.return_value = mock_analyzer_instance

    response = client.post(
        "/analyze",
        files={"file": ("test.pdf", VALID_PDF_CONTENT, "application/pdf")}
    )

    assert response.status_code == 200
    assert response.json() == {
        "Author": ["Unknown"],
        "DateCreated": "Unknown",
        "Language": "Unknown",
        "LastModifiedDate": "Unknown",
        "Title": "Test Document",
        "Summary": "Test summary",
        "Keywords": [],
        "References": [],
        "Citations": []
    }
    mock_doc_handler.assert_called_once()
    mock_handler_instance.save_pdf.assert_called_once()
    mock_read_pdf.assert_called_once_with(mock_handler_instance, "data/document_analysis/test_session/test.pdf")
    mock_analyzer.assert_called_once()
    mock_analyzer_instance.analyze_document.assert_called_once_with("PDF content")

@patch('api.main.FastAPIFileAdapter')
@patch('api.main.DocumentComparatorLLM')
@patch('api.main.DocumentComparator')
def test_compare_endpoint(mock_doc_comparator, mock_comparator_llm, mock_adapter, mock_fitz_open):
    """Test document comparison endpoint"""
    # Mock file adapter
    mock_ref_file = Mock()
    mock_ref_file.name = "ref.pdf"
    mock_ref_file.read.return_value = VALID_PDF_CONTENT
    mock_act_file = Mock()
    mock_act_file.name = "actual.pdf"
    mock_act_file.read.return_value = VALID_PDF_CONTENT
    mock_adapter.side_effect = [mock_ref_file, mock_act_file]

    # Mock DocumentComparator
    mock_comparator_instance = Mock()
    mock_comparator_instance.session_id = "test123"
    mock_comparator_instance.save_uploaded_files.return_value = ("data/document_compare/test123/ref.pdf", "data/document_compare/test123/actual.pdf")
    mock_comparator_instance.combine_documents.return_value = "Combined content"
    mock_doc_comparator.return_value = mock_comparator_instance

    # Mock DocumentComparatorLLM
    mock_llm_instance = Mock()
    mock_df = Mock()
    mock_df.to_dict.return_value = [{"difference": "Test difference"}]
    mock_llm_instance.compare_documents.return_value = mock_df
    mock_comparator_llm.return_value = mock_llm_instance

    response = client.post(
        "/compare",
        files={
            "reference": ("ref.pdf", VALID_PDF_CONTENT, "application/pdf"),
            "actual": ("actual.pdf", VALID_PDF_CONTENT, "application/pdf")
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "rows": [{"difference": "Test difference"}],
        "session_id": "test123"
    }
    mock_doc_comparator.assert_called_once()
    mock_comparator_instance.save_uploaded_files.assert_called_once()
    mock_comparator_instance.combine_documents.assert_called_once()
    mock_comparator_llm.assert_called_once()
    mock_llm_instance.compare_documents.assert_called_once_with("Combined content")