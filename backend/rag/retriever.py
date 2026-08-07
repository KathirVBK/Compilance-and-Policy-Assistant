import sys
import json
from backend.config import Config
from backend.rag.vector_store import VectorStore
from backend.utils.logger import Logger

# Initialize index stores
enterprise_store = VectorStore(Config.ENTERPRISE_INDEX_DIR)
uploaded_store = VectorStore(Config.UPLOADED_INDEX_DIR)

SIMILARITY_THRESHOLD = 0.20

def retrieve(query, k=4, min_score=SIMILARITY_THRESHOLD, target_doc=None):
    """Unified MMR search over both Enterprise and User Uploaded indexes"""
    enterprise_results = enterprise_store.mmr_search(query, k=k, fetch_k=20, filter_doc_title=target_doc)
    uploaded_results = uploaded_store.mmr_search(query, k=k, fetch_k=20, filter_doc_title=target_doc)
    
    # Merge and sort by Cosine Similarity score descending
    all_results = enterprise_results + uploaded_results
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter out results below the similarity score floor threshold
    filtered_results = [r for r in all_results if r.get('score', 0) >= min_score]
    
    Logger.info(f"Retrieved {len(all_results)} MMR candidate chunks, {len(filtered_results)} passed score threshold (>={min_score}).")
    
    # If merging gives more than k, limit to k
    return filtered_results[:k]

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--query':
        query_text = " ".join(sys.argv[2:])
        results = retrieve(query_text)
        print(json.dumps(results, indent=2, ensure_ascii=False))
