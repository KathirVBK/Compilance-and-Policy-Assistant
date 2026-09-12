import os
from backend.config import Config
from backend.rag.vector_store import VectorStore

def compile_enterprise_docs():
    store = VectorStore(Config.ENTERPRISE_INDEX_DIR)
    store.reset()
    
    handbook_path = os.path.join(Config.ENTERPRISE_DOCS_DIR, 'DKT-Employee-Handbook-12.23.pdf')
    if os.path.exists(handbook_path):
        print(f"Loading document from: {handbook_path}")
        from backend.rag.document_loader import load_document
        text = load_document(handbook_path)
            
        print("Chunking, embedding, and saving vectors to FAISS database...")
        success = store.add_document(
            title="DKT Employee Handbook",
            category="Compliance & Operations",
            text=text,
            version="1.0",
            date="2023-12-01",
            author="HR"
        )
        if success:
            print("FAISS Vector database compiled successfully!")
        else:
            print("Error: Vector compilation failed.")
    else:
        print(f"Error: DKT-Employee-Handbook-12.23.pdf not found at {handbook_path}")

if __name__ == '__main__':
    compile_enterprise_docs()
