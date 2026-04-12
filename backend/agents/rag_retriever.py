from layers.vector_store import get_relevant_metric_docs, get_relevant_examples, get_relevant_schema

_MIN_SIMILARITY_DOCS = 1  # ChromaDB doesn't expose similarity thresholds easily; just check non-empty


def retrieve_context(question: str) -> str:
    """
    Queries ChromaDB for schema docs, metric definitions, and similar SQL examples.
    Returns a concatenated context string for the Response Generator (RAG path).
    """
    schema_docs  = get_relevant_schema(question, top_k=3)
    metric_docs  = get_relevant_metric_docs(question, top_k=3)
    examples     = get_relevant_examples(question, top_k=2)

    parts = []
    if schema_docs:
        parts.append(f"## Column Documentation\n{schema_docs}")
    if metric_docs:
        parts.append(f"## Metric Definitions\n{metric_docs}")
    if examples:
        parts.append(f"## Similar Queries\n{examples}")

    if not parts:
        return "No relevant documentation found. Please try rephrasing your question."

    return "\n\n".join(parts)
