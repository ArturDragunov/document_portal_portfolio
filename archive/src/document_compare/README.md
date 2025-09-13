# Document Compare Module

## Overview
This module provides automated PDF document comparison using LLM-powered analysis. It's designed to process pairs of uploaded PDFs, perform side-by-side comparison, and maintain organized session-based storage for tracking comparison results.

## Key Components

### DocumentIngestion (`data_ingestion.py`)
- **Purpose**: Manages PDF file operations and session-based data versioning for document comparison
- **Features**: 
  - Automatic session directory creation with unique identifiers and timestamps
  - PDF validation and secure storage for reference and actual document pairs
  - Text extraction using PyMuPDF (fitz) with page-by-page processing
  - Session-based organization for tracking different comparison runs
  - Document combination functionality for unified processing
  - Optional session cleanup to manage storage

### DocumentComparatorLLM (`document_comparator.py`)
- **Purpose**: Performs intelligent document comparison using LLM analysis
- **Features**:
  - LLM-powered document comparison with specialized prompt templates
  - JSON output parsing with automatic error fixing
  - Structured comparison results using Pydantic models
  - DataFrame output for easy data manipulation and analysis
  - Robust error handling and comprehensive logging

## Workflow
1. **Upload**: Reference and actual PDF files are saved with session tracking
2. **Extract**: Text content is extracted from both PDF documents page-by-page
3. **Combine**: Documents are merged into a unified format for comparison
4. **Compare**: LLM analyzes differences, similarities, and changes between documents
5. **Parse**: Results are formatted into structured DataFrame with error recovery

## Key Dependencies
- `fitz` (PyMuPDF) for PDF processing and text extraction
- `langchain` for LLM integration and output parsing
- `pandas` for structured data output and manipulation
- Custom logging and exception handling systems
- Pydantic models for structured comparison results

## Use Case
Ideal for document versioning workflows where you need to automatically identify changes, additions, deletions, and modifications between different versions of PDF documents. Perfect for compliance tracking, contract analysis, and document revision management.