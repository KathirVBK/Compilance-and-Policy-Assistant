import os
import json
import faiss
import numpy as np
from backend.rag.embeddings import get_embedding
from backend.utils.logger import Logger

class VectorStore:
    def __init__(self, index_dir, dim=1536):
        self.index_dir = index_dir
        self.dim = dim
        self.index_path = os.path.join(index_dir, 'index.bin')
        self.metadata_path = os.path.join(index_dir, 'metadata.json')
        self.index = None
        self.metadata = []
        self.load()

    def load(self):
        """Loads FAISS index and JSON metadata from disk if they exist"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                Logger.info(f"Loaded FAISS index from {self.index_dir} containing {len(self.metadata)} chunks.")
            except Exception as e:
                Logger.error(f"Failed to load FAISS index from {self.index_dir}: {e}")
                self.reset()
        else:
            self.reset()

    def reset(self):
        """Resets the vector index and metadata store to empty state"""
        self.index = faiss.IndexFlatIP(self.dim)
        self.metadata = []
        Logger.info(f"Initialized empty FAISS IndexFlatIP for {self.index_dir}")

    def save(self):
        """Saves current FAISS index and JSON metadata to disk"""
        try:
            os.makedirs(self.index_dir, exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            Logger.info(f"Saved FAISS index and metadata to {self.index_dir}")
        except Exception as e:
            Logger.error(f"Failed to save FAISS index in {self.index_dir}: {e}")

    def add_document(self, title, category, text, version="1.0", date="2025-01-01",
                     author="Unknown", chunk_size=800, overlap=150,
                     tags=None, allowed_roles=None):
        """Chunks document text, generates normalized embeddings, and saves them to index"""
        from backend.rag.text_splitter import split_text
        chunks = split_text(text, chunk_size, overlap)

        # Normalize optional fields
        doc_tags         = tags or []
        doc_allowed_roles = allowed_roles or []   # empty = public (no restriction)

        vectors = []
        new_metadata = []

        for idx, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                chunk_text    = chunk.get('text', '')
                section_title = chunk.get('section', '')
                page_number   = chunk.get('page', 1)
            else:
                chunk_text    = str(chunk)
                section_title = ''
                page_number   = 1

            # Construct prefix with Title, Section, and Page for grounded vector context
            prefix_parts = [title]
            if section_title:
                prefix_parts.append(f"Section: {section_title}")
            prefix_parts.append(f"Page {page_number}")
            prefix    = f"[{' | '.join(prefix_parts)}]\n"
            full_text = prefix + chunk_text

            Logger.info(f"Embedding chunk {idx+1}/{len(chunks)} of '{title}' (Section: '{section_title}', Page: {page_number})...")
            vec = get_embedding(full_text)
            if vec is not None:
                np_vec = np.array(vec, dtype=np.float32)
                norm   = np.linalg.norm(np_vec)
                if norm > 0:
                    np_vec = np_vec / norm
                vectors.append(np_vec)
                parent_section = chunk.get('parent_section', section_title) if isinstance(chunk, dict) else section_title
                end_page       = chunk.get('end_page', page_number) if isinstance(chunk, dict) else page_number
                token_est      = chunk.get('token_estimate', len(chunk_text) // 4) if isinstance(chunk, dict) else len(chunk_text) // 4

                new_metadata.append({
                    "id":             f"{title}_chunk_{idx}_{np.random.randint(1000, 9999)}",
                    "docTitle":       title,
                    "section":        section_title,
                    "parent_section": parent_section,
                    "page":           page_number,
                    "end_page":       end_page,
                    "token_estimate": token_est,
                    "category":       category,
                    "content":        full_text,
                    "rawText":        chunk_text,
                    "version":        version,
                    "date":           date,
                    "author":         author,
                    "tags":           doc_tags,
                    "allowed_roles":  doc_allowed_roles,
                })

        if vectors:
            np_vectors = np.vstack(vectors)
            self.index.add(np_vectors)
            self.metadata.extend(new_metadata)
            self.save()
            Logger.info(f"Successfully added '{title}' ({len(vectors)} chunks) to index.")
            return True
        return False

    def add_structured_chunks(
        self,
        title: str,
        category: str,
        chunks: list,
        version: str = "1.0",
        date: str = "2025-01-01",
        author: str = "Unknown",
        tags: list = None,
        allowed_roles: list = None,
    ) -> bool:
        """
        High-quality indexing path: accepts a list of pre-chunked dicts
        (from text_splitter.split_text on structured blocks) so that section,
        parent_section, page, and token_estimate metadata are all preserved.
        Each chunk dict must have at minimum: { 'text': str }.
        """
        doc_tags          = tags or []
        doc_allowed_roles = allowed_roles or []
        vectors      = []
        new_metadata = []

        for idx, chunk in enumerate(chunks):
            chunk_text     = chunk.get('text', '').strip() if isinstance(chunk, dict) else str(chunk).strip()
            section_title  = chunk.get('section', 'General') if isinstance(chunk, dict) else 'General'
            parent_section = chunk.get('parent_section', section_title) if isinstance(chunk, dict) else section_title
            page_number    = chunk.get('page', 1) if isinstance(chunk, dict) else 1
            end_page       = chunk.get('end_page', page_number) if isinstance(chunk, dict) else page_number
            token_est      = chunk.get('token_estimate', len(chunk_text) // 4) if isinstance(chunk, dict) else len(chunk_text) // 4

            if not chunk_text or len(chunk_text) < 30:
                continue

            prefix = f"[{title} | Section: {section_title} | Page {page_number}]\n"
            full_text = prefix + chunk_text

            Logger.info(f"Embedding structured chunk {idx+1}/{len(chunks)} '{title}' (Section: '{section_title[:40]}', Page: {page_number})...")
            vec = get_embedding(full_text)
            if vec is not None:
                np_vec = np.array(vec, dtype=np.float32)
                norm = np.linalg.norm(np_vec)
                if norm > 0:
                    np_vec = np_vec / norm
                vectors.append(np_vec)
                new_metadata.append({
                    "id":             f"{title}_chunk_{idx}_{np.random.randint(1000, 9999)}",
                    "docTitle":       title,
                    "section":        section_title,
                    "parent_section": parent_section,
                    "page":           page_number,
                    "end_page":       end_page,
                    "token_estimate": token_est,
                    "category":       category,
                    "content":        full_text,
                    "rawText":        chunk_text,
                    "version":        version,
                    "date":           date,
                    "author":         author,
                    "tags":           doc_tags,
                    "allowed_roles":  doc_allowed_roles,
                })

        if vectors:
            np_vectors = np.vstack(vectors)
            self.index.add(np_vectors)
            self.metadata.extend(new_metadata)
            self.save()
            Logger.info(f"Successfully structured-indexed '{title}' ({len(vectors)} chunks) to index.")
            return True
        return False

    def search(self, query, k=4, filter_doc_title=None):
        """Performs cosine similarity search using the FAISS index"""
        if not self.index or self.index.ntotal == 0:
            Logger.warn("Empty FAISS index. Search aborted.")
            return []
            
        vec = get_embedding(query)
        if vec is None:
            Logger.warn("Could not retrieve embedding for query. Search aborted.")
            return []
            
        np_vec = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(np_vec)
        if norm > 0:
            np_vec = np_vec / norm
        np_vec = np_vec.reshape(1, -1)
        
        if filter_doc_title:
            valid_indices = [i for i, m in enumerate(self.metadata) if m['docTitle'] == filter_doc_title]
            if not valid_indices:
                return []
                
            vecs = np.vstack([self.index.reconstruct(i) for i in valid_indices])
            sims = np.dot(vecs, np_vec.T).flatten()
            
            # Sort by similarity
            fetch_count = min(k, len(valid_indices))
            sorted_idx = np.argsort(sims)[::-1][:fetch_count]
            
            results = []
            for i in sorted_idx:
                real_idx = valid_indices[i]
                results.append({
                    **self.metadata[real_idx],
                    "score": float(sims[i])
                })
            return results
        else:
            D, I = self.index.search(np_vec, k)
            
            results = []
            for score, idx in zip(D[0], I[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue
                results.append({
                    **self.metadata[idx],
                    "score": float(score)
                })
            return results

    def mmr_search(self, query, k=4, fetch_k=20, lambda_mult=0.5, filter_doc_title=None):
        """Performs Maximal Marginal Relevance (MMR) search using the FAISS index"""
        if not self.index or self.index.ntotal == 0:
            Logger.warn("Empty FAISS index. MMR Search aborted.")
            return []
            
        query_vec = get_embedding(query)
        if query_vec is None:
            Logger.warn("Could not retrieve embedding for query. MMR Search aborted.")
            return []
            
        np_query = np.array(query_vec, dtype=np.float32)
        norm = np.linalg.norm(np_query)
        if norm > 0:
            np_query = np_query / norm
        np_query = np_query.reshape(1, -1)
        
        # If filtering, we can just extract the valid ones and compute similarity manually
        if filter_doc_title:
            valid_indices = [i for i, m in enumerate(self.metadata) if m['docTitle'] == filter_doc_title]
            if not valid_indices:
                return []
                
            vecs = np.vstack([self.index.reconstruct(i) for i in valid_indices])
            sims = np.dot(vecs, np_query.T).flatten()
            
            # Sort by similarity
            fetch_count = min(fetch_k, len(valid_indices))
            sorted_idx = np.argsort(sims)[::-1][:fetch_count]
            
            candidates = []
            candidate_embeddings = []
            for i in sorted_idx:
                real_idx = valid_indices[i]
                candidates.append({
                    **self.metadata[real_idx],
                    "score": float(sims[i])
                })
                candidate_embeddings.append(vecs[i])
        else:
            # 1. Fetch initial candidates normally
            D, I = self.index.search(np_query, fetch_k)
            
            candidates = []
            candidate_embeddings = []
            for score, idx in zip(D[0], I[0]):
                if idx < 0 or idx >= len(self.metadata):
                    continue
                candidates.append({
                    **self.metadata[idx],
                    "score": float(score)
                })
                try:
                    vec = self.index.reconstruct(int(idx))
                    candidate_embeddings.append(vec)
                except Exception as e:
                    Logger.error(f"Failed to reconstruct vector {idx}: {e}")
                    candidate_embeddings.append(np.zeros(self.dim, dtype=np.float32))
                
        if len(candidates) <= k:
            return candidates[:k]
            
        # 2. Apply MMR
        candidate_embeddings = np.array(candidate_embeddings)
        selected = []
        
        # Start with the most similar
        selected.append(0)
        
        while len(selected) < k:
            best_score = -np.inf
            best_idx = -1
            
            for i in range(len(candidates)):
                if i in selected:
                    continue
                
                # Relevance to query
                sim_to_query = candidates[i]['score']
                
                # Max similarity to already selected
                max_sim_to_selected = max([np.dot(candidate_embeddings[i], candidate_embeddings[s]) for s in selected])
                
                # MMR Score
                mmr_score = lambda_mult * sim_to_query - (1 - lambda_mult) * max_sim_to_selected
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
                    
            if best_idx != -1:
                selected.append(best_idx)
            else:
                break
                
        return [candidates[i] for i in selected]

    def get_parent_context(self, chunk_id: str) -> str:
        """
        Parent-Child Retrieval: given a child chunk ID, returns concatenated text
        of all sibling chunks sharing the same parent_section and docTitle.
        Falls back to the chunk's own content if no siblings found.
        """
        # Find the target chunk
        target = next((m for m in self.metadata if m.get("id") == chunk_id), None)
        if not target:
            return ""

        parent_sec = target.get("parent_section", target.get("section", ""))
        doc_title  = target.get("docTitle", "")

        # Collect all sibling chunks in the same parent section
        siblings = [
            m for m in self.metadata
            if m.get("docTitle") == doc_title
            and m.get("parent_section", m.get("section", "")) == parent_sec
        ]

        if len(siblings) <= 1:
            return target.get("rawText", target.get("content", ""))

        # Sort siblings by page then chunk index order
        siblings.sort(key=lambda m: (m.get("page", 0),))
        return " ".join(s.get("rawText", s.get("content", "")) for s in siblings)
