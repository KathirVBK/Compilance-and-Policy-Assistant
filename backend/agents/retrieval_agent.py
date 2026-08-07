from backend.rag import retriever
from backend.utils.logger import Logger

def retrieve_context(query, k=6, target_doc=None):
    """Retrieval Agent: retrieves contextual chunks from the FAISS database"""
    Logger.info(f"Retrieval Agent querying vector store for: '{query}' (k={k}, target_doc={target_doc})")
    results = retriever.retrieve(query, k=k, target_doc=target_doc)
    Logger.info(f"Retrieved {len(results)} matches above relevance threshold.")
    return results
