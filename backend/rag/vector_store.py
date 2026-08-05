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

    def add_document(self, title, category, text, version="1.0", date="2025-01-01", author="Unknown", chunk_size=800, overlap=160):
        """Chunks document text, generates normalized embeddings, and saves them to index"""
        from backend.rag.text_splitter import split_text
        chunks = split_text(text, chunk_size, overlap)
        
        vectors = []
        new_metadata = []
        
        for idx, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                chunk_text = chunk.get('text', '')
                section_title = chunk.get('section', '')
                page_number = chunk.get('page', 1)
            else:
                chunk_text = str(chunk)
                section_title = ''
                page_number = 1

            # Construct prefix with Title, Section, and Page for grounded vector context
            prefix_parts = [title]
            if section_title:
                prefix_parts.append(f"Section: {section_title}")
            prefix_parts.append(f"Page {page_number}")
            prefix = f"[{' | '.join(prefix_parts)}]\n"
            full_text = prefix + chunk_text
            
            Logger.info(f"Embedding chunk {idx+1}/{len(chunks)} of '{title}' (Section: '{section_title}', Page: {page_number})...")
            vec = get_embedding(full_text)
            if vec is not None:
                np_vec = np.array(vec, dtype=np.float32)
                norm = np.linalg.norm(np_vec)
                if norm > 0:
                    np_vec = np_vec / norm
                vectors.append(np_vec)
                new_metadata.append({
                    "id": f"{title}_chunk_{idx}_{np.random.randint(1000, 9999)}",
                    "docTitle": title,
                    "section": section_title,
                    "page": page_number,
                    "category": category,
                    "content": full_text,
                    "rawText": chunk_text,
                    "version": version,
                    "date": date,
                    "author": author
                })

        if vectors:
            np_vectors = np.vstack(vectors)
            self.index.add(np_vectors)
            self.metadata.extend(new_metadata)
            self.save()
            Logger.info(f"Successfully added '{title}' ({len(vectors)} chunks) to index.")
            return True
        return False

    def search(self, query, k=4):
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
