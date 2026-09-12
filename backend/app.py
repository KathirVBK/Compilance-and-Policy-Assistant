import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import Config
from backend.api.routes import router
from backend.api.auth_routes import auth_router
from backend.api.admin_routes import admin_router
from backend.rag.retriever import enterprise_store
from backend.utils.logger import Logger

app = FastAPI(
    title="Enterprise Compliance & Operations AI Assistant API",
    description="Multi-agent compliance graph engine backed by FAISS vector store.",
    version="3.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(router,       prefix="/api")
app.include_router(auth_router,  prefix="/api/auth")
app.include_router(admin_router, prefix="/api/admin")


@app.on_event("startup")
async def startup_event():
    Logger.info("Starting up Enterprise Compliance FastAPI Server v3.0...")

    # Auto-index DKT Employee Handbook if FAISS enterprise index is empty
    if len(enterprise_store.metadata) == 0:
        Logger.info("FAISS Enterprise Index is empty. Auto-indexing DKT-Employee-Handbook-12.23.pdf (structured path)...")
        coc_path = os.path.join(Config.ENTERPRISE_DOCS_DIR, 'DKT-Employee-Handbook-12.23.pdf')

        if os.path.exists(coc_path):
            try:
                from backend.rag.document_loader import load_document_structured
                from backend.rag.text_splitter import split_text

                # 1. Page-aware structured extraction
                blocks = load_document_structured(coc_path)
                if blocks:
                    # 2. Hierarchical + semantic chunking (400-700 tokens, 12% overlap)
                    chunks = split_text(blocks)
                    Logger.info(f"Produced {len(chunks)} hierarchical chunks from DKT-Employee-Handbook-12.23.pdf")

                    # 3. Use structured indexing path to preserve section/page metadata
                    success = enterprise_store.add_structured_chunks(
                        title="DKT Employee Handbook",
                        category="Compliance & Ethics",
                        chunks=chunks,
                        version="2023",
                        date="2023-12-01",
                        author="DKT International"
                    )
                    if success:
                        Logger.info("Auto-indexing complete! DKT Employee Handbook indexed with full section/page metadata.")
                    else:
                        Logger.error("Auto-indexing failed to write vectors.")
                else:
                    Logger.error("Structured extraction produced no blocks from DKT-Employee-Handbook-12.23.pdf.")
            except Exception as e:
                Logger.error(f"Auto-indexing error: {e}")
        else:
            Logger.warn(f"DKT-Employee-Handbook-12.23.pdf missing from {Config.ENTERPRISE_DOCS_DIR}.")
    Logger.info("Server ready. Auth routes: /api/auth | Admin routes: /api/admin")


if __name__ == '__main__':
    uvicorn.run("backend.app:app", host="0.0.0.0", port=Config.PORT, reload=True)
