import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import Config
from backend.api.routes import router
from backend.rag.retriever import enterprise_store
from backend.utils.logger import Logger

app = FastAPI(
    title="Enterprise Compliance & Operations AI Assistant API",
    description="Multi-agent compliance graph engine backed by FAISS vector store.",
    version="2.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for the hackathon prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    Logger.info("Starting up Enterprise Compliance FastAPI Server...")
    
    # Check if the FAISS enterprise index is empty, if so, trigger compilation
    if len(enterprise_store.metadata) == 0:
        Logger.info("FAISS Enterprise Index is empty. Auto-compiling from handbook_2025.txt...")
        handbook_path = os.path.join(Config.ENTERPRISE_DOCS_DIR, 'handbook_2025.txt')
        
        if os.path.exists(handbook_path):
            try:
                with open(handbook_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                success = enterprise_store.add_document(
                    title="Employee Handbook (Endeavors)",
                    category="Compliance & Operations",
                    text=text,
                    version="2.0",
                    date="2025-01-01",
                    author="CFO & HR Office"
                )
                if success:
                    Logger.info("Auto-compilation complete! handbook_2025 indexed successfully.")
                else:
                    Logger.error("Auto-compilation failed to write vectors.")
            except Exception as e:
                Logger.error(f"Auto-compilation error: {e}")
        else:
            Logger.warn(f"handbook_2025.txt missing from {Config.ENTERPRISE_DOCS_DIR}. Please place file to index.")

if __name__ == '__main__':
    uvicorn.run("backend.app:app", host="0.0.0.0", port=Config.PORT, reload=True)
