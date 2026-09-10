from typing import Optional
from backend.rag import retriever
from backend.utils.logger import Logger

def retrieve_context(query: str, k: int = 6, target_doc: Optional[str] = None, user_role: Optional[str] = None):
    """Retrieval Agent: retrieves contextual chunks from the FAISS database with RBAC filtering"""
    Logger.info(f"Retrieval Agent querying vector store for: '{query}' (k={k}, target_doc={target_doc}, role={user_role})")
    results = retriever.retrieve(query, k=k, target_doc=target_doc, user_role=user_role)
    Logger.info(f"Retrieved {len(results)} matches above relevance threshold (after RBAC filtering).")
    return results
