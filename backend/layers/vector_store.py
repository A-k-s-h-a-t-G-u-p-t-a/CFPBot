import os

import chromadb
from fastembed import TextEmbedding

_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../data/chroma_db")
_model  = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
_client = chromadb.PersistentClient(path=_CHROMA_PATH)


def _embed(text: str) -> list[float]:
    return list(_model.embed([text]))[0].tolist()


def _query_collection(name: str, question: str, top_k: int) -> str:
    try:
        col = _client.get_collection(name)
        n   = min(top_k, col.count())
        if n == 0:
            return ""
        results = col.query(query_embeddings=[_embed(question)], n_results=n)
        return "\n".join(results["documents"][0])
    except Exception:
        return ""


def get_relevant_schema(question: str, top_k: int = 3) -> str:
    return _query_collection("schema_docs", question, top_k)


def get_relevant_metric_docs(question: str, top_k: int = 3) -> str:
    return _query_collection("metric_docs", question, top_k)


def get_relevant_examples(question: str, top_k: int = 2) -> str:
    return _query_collection("sample_queries", question, top_k)


def get_collection_count(name: str) -> int:
    try:
        return _client.get_collection(name).count()
    except Exception:
        return 0
