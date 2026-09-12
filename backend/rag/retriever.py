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
    if not allowed:
        return True
    if user_role == "admin":
        return True
    return user_role in allowed


def retrieve(
    query: str,
    k: int = 4,
    min_score: float = SIMILARITY_THRESHOLD,
    target_doc: Optional[str] = None,
    user_role: Optional[str] = None,
    category_filter: Optional[str] = None,
    version_filter: Optional[str] = None,
    date_after: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Single-query retrieval (used internally by multi_retrieve).
    Applies similarity threshold, RBAC, and optional metadata filters.
    """
    enterprise_results = enterprise_store.search(query, k=k, filter_doc_title=target_doc)
    uploaded_results   = uploaded_store.search(query,   k=k, filter_doc_title=target_doc)

    all_results = enterprise_results + uploaded_results
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Filter 1: similarity score floor
    filtered = [r for r in all_results if r.get("score", 0) >= min_score]

    # Filter 2: RBAC
    if user_role is not None:
        before = len(filtered)
        filtered = [r for r in filtered if _is_accessible(r, user_role)]
        removed = before - len(filtered)
        if removed:
            Logger.info(f"RBAC: filtered {removed} restricted chunk(s) for role '{user_role}'.")

    # Filter 3: Optional metadata filters
    if category_filter:
        filtered = [r for r in filtered
                    if r.get("category", "").lower() == category_filter.lower()]

    if version_filter:
        filtered = [r for r in filtered if r.get("version", "") == version_filter]

    if date_after:
        filtered = [r for r in filtered if r.get("date", "0000") >= date_after]

    return filtered[:k]


def multi_retrieve(
    queries: List[str],
    fetch_k: int = 8,
    final_k: int = 20,
    min_score: float = SIMILARITY_THRESHOLD,
    target_doc: Optional[str] = None,
    user_role: Optional[str] = None,
    category_filter: Optional[str] = None,
    version_filter: Optional[str] = None,
    date_after: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Multi-Query Retrieval with PARALLEL FAISS searches.
    Runs all query variants concurrently using ThreadPoolExecutor,
    deduplicates results by chunk ID, returns up to final_k unique chunks
    sorted by best cosine score for downstream cross-encoder reranking.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _search_one(q: str) -> List[Dict[str, Any]]:
        return retrieve(
            q,
            k=fetch_k,
            min_score=min_score,
            target_doc=target_doc,
            user_role=user_role,
            category_filter=category_filter,
            version_filter=version_filter,
            date_after=date_after,
        )

    seen_ids: set = set()
    merged: List[Dict[str, Any]] = []

    # Run all query variants in parallel
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        futures = {executor.submit(_search_one, q): q for q in queries}
        for future in as_completed(futures):
            try:
                results = future.result()
                for r in results:
                    chunk_id = r.get("id", "")
                    if chunk_id not in seen_ids:
                        seen_ids.add(chunk_id)
                        merged.append(r)
            except Exception as e:
                Logger.warn(f"Multi-retrieve: a query variant failed — {e}")

    # Sort deduplicated pool by cosine score desc
    merged.sort(key=lambda x: x.get("score", 0), reverse=True)

    Logger.info(
        f"Multi-retrieve [PARALLEL]: {len(queries)} queries → {len(merged)} unique candidates "
        f"(cap={final_k}, threshold={min_score})."
    )
    return merged[:final_k]



if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--query":
        query_text = " ".join(sys.argv[2:])
        results = retrieve(query_text)
        print(json.dumps(results, indent=2, ensure_ascii=False))



