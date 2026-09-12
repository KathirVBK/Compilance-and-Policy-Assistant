from typing import Optional, List, Dict, Any
from backend.rag import retriever
from backend.rag.retriever import enterprise_store, uploaded_store
from backend.rag.reranker import rerank_chunks
from backend.agents.query_rewriter import generate_multi_queries
from backend.utils.logger import Logger

# ── Tuning constants ──────────────────────────────────────────────────────────
FETCH_K     = 8   # candidates per query variant from FAISS (reduced for speed)
FINAL_TOP_K = 5   # final chunks after cross-encoder reranking


def _expand_parent_context(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parent-Child Retrieval expansion.
    Augments the chunk's rawText with surrounding sibling context from
    the same parent_section, providing the LLM with wider coherent context.
    """
    chunk_id = chunk.get("id", "")
    if not chunk_id:
        return chunk

    # Search both stores
    parent_text = None
    for store in [enterprise_store, uploaded_store]:
        pt = store.get_parent_context(chunk_id)
        if pt and len(pt) > len(chunk.get("rawText", "")):
            parent_text = pt
            break

    if parent_text:
        chunk = dict(chunk)  # Don't mutate original
        chunk["parent_context"] = parent_text
        Logger.info(
            f"Parent expansion: chunk '{chunk_id[:20]}' expanded "
            f"({len(chunk.get('rawText',''))} → {len(parent_text)} chars)"
        )
    return chunk


def retrieve_context(
    query: str,
    k: int = FINAL_TOP_K,
    target_doc: Optional[str] = None,
    user_role: Optional[str] = None,
    category_filter: Optional[str] = None,
    version_filter: Optional[str] = None,
    date_after: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Advanced Retrieval Agent Pipeline:
    1. Multi-Query Generation     — 2-4 LLM-rewritten query variants
    2. Multi-Query FAISS Retrieval — parallel search, dedup, top 10-20 candidates
    3. Cross-Encoder Reranking    — LLM scores each candidate (0-10), keeps top k
    4. Parent-Child Expansion     — augments each result with parent section context
    """
    Logger.info(f"Retrieval Agent [ADVANCED] | query='{query[:80]}' | role={user_role} | doc={target_doc}")

    # ── Stage 1: Multi-Query Generation ──────────────────────────────────────
    queries = generate_multi_queries(query)

    # ── Stage 2: Multi-Query FAISS Retrieval ─────────────────────────────────
    candidates = retriever.multi_retrieve(
        queries=queries,
        fetch_k=FETCH_K,
        final_k=FETCH_K * len(queries),  # e.g. 8 * 4 = 32 max candidates for reranker
        target_doc=target_doc,
        user_role=user_role,
        category_filter=category_filter,
        version_filter=version_filter,
        date_after=date_after,
    )

    if not candidates:
        Logger.warn("Retrieval Agent: No candidates found above similarity threshold.")
        return []

    # ── Stage 3: Cross-Encoder Reranking ─────────────────────────────────────
    reranked = rerank_chunks(query=query, candidates=candidates, top_k=k)

    # ── Stage 4: Parent-Child Context Expansion ───────────────────────────────
    enriched = [_expand_parent_context(chunk) for chunk in reranked]

    Logger.info(
        f"Retrieval Agent complete: {len(queries)} queries → "
        f"{len(candidates)} candidates → {len(enriched)} enriched final chunks."
    )
    return enriched

