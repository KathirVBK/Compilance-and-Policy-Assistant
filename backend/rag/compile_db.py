import os
from backend.config import Config
from backend.rag.vector_store import VectorStore

def compile_enterprise_docs():
    store = VectorStore(Config.ENTERPRISE_INDEX_DIR)
    store.reset()
    
    handbook_path = os.path.join(Config.ENTERPRISE_DOCS_DIR, 'handbook_2025.txt')
    if os.path.exists(handbook_path):
        print(f"Loading document from: {handbook_path}")
        with open(handbook_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        print("Chunking, embedding, and saving vectors to FAISS database...")
        success = store.add_document(
            title="Employee Handbook (Endeavors)",
            category="Compliance & Operations",
            text=text,
            version="2.0",
            date="2025-01-01",
            author="CFO & HR Office"
        )
        if success:
            print("FAISS Vector database compiled successfully!")
        else:
            print("Error: Vector compilation failed.")
    else:
        print(f"Error: handbook_2025.txt not found at {handbook_path}")

if __name__ == '__main__':
    compile_enterprise_docs()
