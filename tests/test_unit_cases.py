# tests/test_unit_cases.py

import pytest
from fastapi.testclient import TestClient
from api.main import app   # or your FastAPI entrypoint

client = TestClient(app)

def test_home():
    """Check if the home page is being called"""
    response = client.get("/") # home page of the application (index.html)
    assert response.status_code == 200 # status ok
    assert "Document Portal" in response.text
