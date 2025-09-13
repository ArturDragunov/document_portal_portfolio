# Document Analyzer Module

## Overview
This module provides automated PDF document analysis using LLM-powered metadata extraction. It's designed to process uploaded PDFs, extract structured information, and maintain organized session-based storage.

## Key Components

### DocumentHandler (`data_ingestion.py`)
- **Purpose**: Manages PDF file operations and session-based data versioning
- **Features**: 
  - Automatic session directory creation with timestamps
  - PDF validation and secure storage
  - Text extraction using PyMuPDF (fitz)
  - Session-based organization for tracking different analysis runs

### DocumentAnalyzer (`data_analysis.py`)
- **Purpose**: Extracts structured metadata from document text using LLM
- **Features**:
  - LLM-powered document analysis with prompt templates
  - JSON output parsing with automatic error fixing
  - Structured metadata extraction (uses Pydantic models)
  - Robust error handling and logging

## Workflow
1. **Upload**: PDF files are saved with session tracking
2. **Extract**: Text content is extracted from PDF pages
3. **Analyze**: LLM processes text to extract structured metadata
4. **Parse**: Results are parsed into structured JSON format with error recovery

## Key Dependencies
- `fitz` (PyMuPDF) for PDF processing
- `langchain` for LLM integration and output parsing
- Custom logging and exception handling
- Pydantic models for structured output

## Use Case
Ideal for document processing pipelines where you need to automatically extract metadata, summaries, or structured information from PDF documents at scale.