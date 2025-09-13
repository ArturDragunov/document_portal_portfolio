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

def test_resolve_dir_creates_session(tmp_path):
    ingestor = ChatIngestor(temp_base=tmp_path, faiss_base=tmp_path, use_session_dirs=True)
    result = ingestor._resolve_dir(tmp_path)
    assert result.exists()
    assert ingestor.session_id in str(result)

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

# UNIT TESTS
@patch('src.document_analyzer.data_analysis.ModelLoader')
@patch('src.document_analyzer.data_analysis.PROMPT_REGISTRY')
def test_document_analyzer_initialization(mock_prompt_registry, mock_model_loader):
    """Test DocumentAnalyzer initializes correctly"""
    mock_loader = Mock()
    mock_llm = Mock()
    mock_loader.load_llm.return_value = mock_llm
    mock_model_loader.return_value = mock_loader
    mock_prompt_registry.__getitem__.return_value = Mock()
    
    analyzer = DocumentAnalyzer()
    assert analyzer.llm == mock_llm
    mock_loader.load_llm.assert_called_once()

def test_doc_handler_initialization():
    """Test DocHandler initializes with proper paths"""
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = DocHandler(data_dir=temp_dir, session_id="test123")
        assert handler.session_id == "test123"
        assert temp_dir in handler.session_path
        assert os.path.exists(handler.session_path)

@patch('src.document_ingestion.data_ingestion.fitz.open')
def test_doc_handler_read_pdf(mock_fitz_open):
    """Test PDF reading functionality"""
    mock_doc = Mock()
    mock_doc.is_encrypted = False
    mock_doc.page_count = 2
    mock_page1 = Mock()
    mock_page1.get_text.return_value = "Page 1 content"
    mock_page2 = Mock()
    mock_page2.get_text.return_value = "Page 2 content"
    mock_doc.load_page.side_effect = [mock_page1, mock_page2]
    mock_fitz_open.return_value.__enter__.return_value = mock_doc
    
    handler = DocHandler()
    result = handler.read_pdf("test.pdf")
    
    assert "Page 1 content" in result
    assert "Page 2 content" in result
    assert "--- Page 1 ---" in result
    assert "--- Page 2 ---" in result

@patch('src.document_chat.retrieval.ModelLoader')
@patch('src.document_chat.retrieval.PROMPT_REGISTRY')
def test_conversational_rag_initialization(mock_prompt_registry, mock_model_loader):
    """Test ConversationalRAG initializes properly"""
    mock_loader = Mock()
    mock_llm = Mock()
    mock_loader.load_llm.return_value = mock_llm
    mock_model_loader.return_value = mock_loader
    mock_prompt_registry.__getitem__.return_value = Mock()
    
    rag = ConversationalRAG(session_id="test123")
    
    assert rag.session_id == "test123"
    assert rag.retriever is None
    assert rag.chain is None

def test_faiss_manager_initialization():
    """Test FaissManager initializes correctly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('src.document_ingestion.data_ingestion.ModelLoader'):
            fm = FaissManager(Path(temp_dir))
            assert fm.index_dir == Path(temp_dir)
            assert fm._meta == {"rows": {}}
            assert not fm._exists()

