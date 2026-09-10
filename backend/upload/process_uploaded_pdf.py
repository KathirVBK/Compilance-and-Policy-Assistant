import os
from backend.rag.document_loader import load_document
from backend.rag.retriever import uploaded_store
from backend.utils.logger import Logger

def process_and_index_file(
    file_path: str,
    title: str,
    category: str,
    version: str = "1.0",
    date: str = "2025-01-01",
    author: str = "Unknown",
    tags: list = None,
    allowed_roles: list = None
):
    """Loads file text, chunks, embeds, and indexes into the uploaded index vector store.
    Supports tags (for category filtering) and allowed_roles (for RBAC)."""
    Logger.info(f"Processing and indexing uploaded document: {file_path}")

    text = load_document(file_path)
    if not text or text.strip() == "":
        Logger.error("Empty text extracted from document. Indexing skipped.")
        return False

    # Index document in FAISS store with optional metadata
    success = uploaded_store.add_document(
        title=title,
        category=category,
        text=text,
        version=version,
        date=date,
        author=author,
        tags=tags or [],
        allowed_roles=allowed_roles or []
    )

    # Remove original temporary upload file after indexing
    try:
        os.remove(file_path)
        Logger.info("Removed temporary upload source file.")
    except Exception as e:
        Logger.warn(f"Failed to remove temporary file {file_path}: {e}")

    return success
