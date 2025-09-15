# Document Portal

**Document Portal** is a production-ready FastAPI application for document ingestion, analysis, and conversational interaction with files. It supports:

* **Analysis** – extract content and metadata from uploaded PDFs
* **Compare** – perform **LLM-based page-by-page comparison** between two documents
* **Chat** – upload documents, embed them into a FAISS index, and run **conversational RAG queries** with support for tables (Camelot) and images (EZOCR)

The project is fully containerized and deployed with **AWS ECS (Fargate)**, **ECR**, and **CI/CD pipelines via GitHub Actions**. It includes **unit/integration testing**, logging, and secure secret management.

---

## 🚀 Features

* Modular **FastAPI backend** with OOP architecture
* Document analysis, comparison, and chat with LLMs
* Table extraction and OCR
* Vector database powered by **FAISS**
* **DeepEval** integration for RAG evaluation
* CI/CD with GitHub Actions → AWS ECR → ECS (Fargate)
* Logging & monitoring with **CloudWatch**
* Secrets & credentials handled via **AWS Secrets Manager** and **IAM**

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, Python
* **Data/AI**: LangChain, FAISS, Camelot, EasyOCR
* **Testing**: Pytest (unit + integration), DeepEval
* **DevOps**: Docker, GitHub Actions, AWS ECS (Fargate), AWS ECR, CloudWatch, IAM, Secrets Manager
* **Others**: Modular OOP design, custom exception handling, logging & data archiving

---

## ⚡ Quickstart

### Prerequisites

* Python 3.10+
* [uv](https://github.com/astral-sh/uv) package manager
* Docker (for containerized deployment)
* API keys:

  * [Groq](https://console.groq.com/keys)
  * [Gemini](https://ai.google.dev/gemini-api/docs/models)
  
### Setup

```bash
# Sync environment from pyproject.toml
uv sync

# Run the FastAPI app
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## 📡 API Endpoints

* `POST /analyze` – analyze a single PDF (metadata + content)
* `POST /compare` – compare two PDFs page by page using LLM
* `POST /chat/index` – create FAISS index from uploaded files (with OCR support)
* `POST /chat/query` – query the indexed documents with conversational RAG
* `GET /health` – service health check

---

## 🧪 Testing

```bash
pytest tests/
```

Includes **unit tests and integration tests**.

---

## 📦 Deployment

* CI/CD with **GitHub Actions** runs tests → builds Docker image → pushes to **AWS ECR**
* Image deployed to **AWS ECS (Fargate)** with public endpoint
* Logs available via **AWS CloudWatch**

---

## 📖 Demo

Download document-portal-demo.mp4 or aend me a message for a live-project link: artur.dragunov.career@gmail.com
---