import sys
import json
from typing import Optional, List, Dict, Any
from backend.config import Config
from backend.rag.vector_store import VectorStore
from backend.utils.logger import Logger

# Initialize index stores
enterprise_store = VectorStore(Config.ENTERPRISE_INDEX_DIR)
uploaded_store   = VectorStore(Config.UPLOADED_INDEX_DIR)

SIMILARITY_THRESHOLD = 0.20


def _is_accessible(chunk: Dict[str, Any], user_role: Optional[str]) -> bool:
    """
    Returns True if the chunk is accessible to the given role.
    A chunk is accessible when:
      - It has no role restriction (allowed_roles is empty / missing), OR
      - The user_role is 'admin' (admins see everything), OR
      - The user_role is explicitly listed in allowed_roles.
    """
    allowed = chunk.get("allowed_roles", [])
    if not allowed:          # No restriction — public
        return True
    if user_role == "admin":  # Admins bypass all restrictions
        return True
    return user_role in allowed


def retrieve(
    query: str,
    k: int = 4,
    min_score: float = SIMILARITY_THRESHOLD,
    target_doc: Optional[str] = None,
    user_role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves top-k relevant chunks from both stores, applies similarity
    threshold filtering, and enforces RBAC based on user_role.
    """
    enterprise_results = enterprise_store.search(query, k=k, filter_doc_title=target_doc)
    uploaded_results   = uploaded_store.search(query,   k=k, filter_doc_title=target_doc)

    # Merge and sort by Cosine Similarity score descending
    all_results = enterprise_results + uploaded_results
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Filter 1: similarity score floor
    filtered = [r for r in all_results if r.get("score", 0) >= min_score]

    # Filter 2: RBAC — remove chunks the user is not allowed to see
    if user_role is not None:
        before_rbac = len(filtered)
        filtered = [r for r in filtered if _is_accessible(r, user_role)]
        removed = before_rbac - len(filtered)
        if removed:
            Logger.info(f"RBAC: Filtered out {removed} restricted chunk(s) for role '{user_role}'.")

    Logger.info(
        f"Retrieved {len(all_results)} candidate chunks, "
        f"{len(filtered)} passed score threshold (>={min_score}) and RBAC check."
    )

    # If merging gives more than k, limit to k
    return filtered[:k]


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--query":
        query_text = " ".join(sys.argv[2:])
        results = retrieve(query_text)
        print(json.dumps(results, indent=2, ensure_ascii=False))
