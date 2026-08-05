from backend.rag import retriever
from backend.utils.logger import Logger

def retrieve_context(query, k=6):
    """Retrieval Agent: retrieves contextual chunks from the FAISS database"""
    Logger.info(f"Retrieval Agent querying vector store for: '{query}' (k={k})")
    results = retriever.retrieve(query, k=k)
    Logger.info(f"Retrieved {len(results)} matches above relevance threshold.")
    return results
