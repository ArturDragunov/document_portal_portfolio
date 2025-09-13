import os
import json
from typing import List, Dict, Any, Optional
import deepeval
from deepeval.test_case import LLMTestCase
from deepeval.dataset import Golden, EvaluationDataset
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric, ContextualRecallMetric, ContextualPrecisionMetric
import re
from src.document_chat.retrieval import ConversationalRAG
from pathlib import Path

FAISS_BASE = os.getenv("FAISS_BASE", "faiss_index")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")

def normalize_text(t: Optional[str]) -> str:
  """Extended normalizer for RAG evaluation comparison."""
  if t is None:
    return ""
  
  text = str(t)
  
  # Remove extra whitespace and normalize
  text = re.sub(r'\s+', ' ', text.strip())
  
  # Lowercase
  text = text.lower()
  
  # Remove extra periods/dots
  text = re.sub(r'\.+', '.', text)
  
  # Final whitespace cleanup
  return ' '.join(text.split())

def load_goldens(path: str) -> List[Golden]:
    """Loads a JSON list of goldens from disk"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Goldens file not found: {path}")
    goldens = json.loads(p.read_text(encoding="utf-8"))
    test_cases = []
    for g in goldens:
      golden = Golden(
        input = g["input"],
        expected_output= normalize_text(g.get("expected_output", "")))
      test_cases.append(golden)
    return test_cases


def run_rag_once(question: str, session_id: str, k: int = 5, index_dir_base: str = FAISS_BASE):
    """
    Run RAG pipeline for a single question against an existing FAISS index session.
    Returns: dict { actual_output: str, retrieval_context: List[str] }
    """
    index_path = os.path.join(index_dir_base, session_id)
    if not os.path.isdir(index_path):
        raise FileNotFoundError(f"FAISS index folder not found: {index_path}")

    # create rag and load retriever from FAISS
    rag = ConversationalRAG(session_id=session_id)
    rag.load_retriever_from_faiss(index_path=index_path, k=k, index_name=FAISS_INDEX_NAME)

    # many retrievers expose get_relevant_documents(query)
    retrieval_docs = rag.retriever.invoke(question)

    # Convert docs -> strings
    retrieval_context = []
    for d in retrieval_docs:
        text = d.page_content
        retrieval_context.append(str(text))

    # invoke to get the answer (uses your chain)
    answer = rag.invoke(question, chat_history=[])
    return {"actual_output": normalize_text(answer), "retrieval_context": [normalize_text(x) for x in retrieval_context]}


def build_deepeval_testcases_from_goldens(goldens: List[Golden], session_id: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    goldens: EvaluationDataset of Goldens
    Returns list of test_case dicts usable by deepeval evaluator.
    """

    test_cases: List[LLMTestCase] = []
    for g in goldens:
        q = g.input
        expected = normalize_text(g.expected_output)
        out = run_rag_once(q, session_id=session_id, k=k)
        tc = LLMTestCase(
            input=q,
            actual_output=out["actual_output"],
            expected_output=expected,
            retrieval_context=out["retrieval_context"],
        )
        test_cases.append(tc)
    return test_cases


def evaluate_with_deepeval(test_cases: List[LLMTestCase]) -> Any:
    """
    Uses current deepeval.evaluate API to evaluate the test_cases.
    Returns deepeval.evaluate
    """
    metrics = [
        AnswerRelevancyMetric(),
        FaithfulnessMetric(),
        ContextualRelevancyMetric(),
        ContextualRecallMetric(),
        ContextualPrecisionMetric(),
    ]
    results = deepeval.evaluate(test_cases, metrics=metrics)
    return results
