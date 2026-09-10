import os
import shutil
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List

from backend.config import Config
from backend.graph.graph import run_workflow
from backend.rag.retriever import enterprise_store, uploaded_store
from backend.rag.document_loader import load_document
from backend.upload.upload_handler import save_uploaded_file
from backend.upload.process_uploaded_pdf import process_and_index_file
from backend.speech import whisper, tts
from backend.auth.auth_manager import AuthManager
from backend.utils.audit_logger import AuditLogger
from backend.utils.logger import Logger

router = APIRouter()


# ─── Helper: extract user from token (non-blocking — returns anonymous if no token) ──
def _get_user_from_request(authorization: Optional[str]) -> dict:
    """Returns user dict from Bearer token, or a default anonymous employee dict."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
        user  = AuthManager.get_user_from_token(token)
        if user:
            return user
    return {"username": "anonymous", "role": "employee", "name": "Anonymous"}


# ─── Request Models ───────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = None
    history: Optional[list] = None
    session_id: Optional[str] = None
    target_doc: Optional[str] = None
    user_role: Optional[str] = None     # Role sent by authenticated frontend

class TTSRequest(BaseModel):
    text: str


# ─── Models ───────────────────────────────────────────────────────────────────
@router.get("/models")
async def get_models():
    return [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gpt-4.1-nano",     "name": "GPT 4.1 Nano"},
        {"id": "gpt-4o-mini-tts",  "name": "GPT 4o Mini TTS"},
        {"id": "whisper-1",        "name": "Whisper 1 (Audio)"},
        {"id": "nova-micro",       "name": "Nova Micro"}
    ]


# ─── Query ────────────────────────────────────────────────────────────────────
@router.post("/query")
async def process_query(req: QueryRequest, authorization: Optional[str] = Header(None)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Resolve user role: prefer token-derived role over client-sent role (security)
    caller = _get_user_from_request(authorization)
    effective_role = caller["role"]  # Token-derived role takes precedence

    try:
        response = run_workflow(
            req.query, req.model, req.history,
            req.session_id, req.target_doc,
            user_role=effective_role
        )

        # Audit log every query (non-blocking)
        is_escalated = response and response.get("status") == "escalated"
        AuditLogger.log(
            action="escalate" if is_escalated else "query",
            user=caller["username"],
            role=effective_role,
            severity="high" if is_escalated else "info",
            details=f"Query: '{req.query[:120]}'",
            session_id=req.session_id
        )
        return response
    except Exception as e:
        Logger.error(f"Error processing graph workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Documents ────────────────────────────────────────────────────────────────
@router.get("/documents")
async def get_documents(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Returns all active documents, optionally filtered by category or tag.
    RBAC: non-admin users only see docs they are allowed to access."""
    caller = _get_user_from_request(authorization)
    user_role = caller["role"]

    docs = []
    seen = set()

    all_metadata = enterprise_store.metadata + uploaded_store.metadata
    for meta in all_metadata:
        title = meta["docTitle"]
        if title in seen:
            continue

        # RBAC: skip docs the user is not allowed to see
        allowed = meta.get("allowed_roles", [])
        if allowed and user_role != "admin" and user_role not in allowed:
            continue

        # Category filter
        if category and meta.get("category", "").lower() != category.lower():
            continue

        # Tag filter
        if tag and tag.lower() not in [t.lower() for t in meta.get("tags", [])]:
            continue

        seen.add(title)
        docs.append({
            "id":            meta.get("id", title),
            "title":         title,
            "category":      meta.get("category", "General"),
            "version":       meta.get("version", "1.0"),
            "date":          meta.get("date", "Unknown"),
            "author":        meta.get("author", "Unknown"),
            "tags":          meta.get("tags", []),
            "allowed_roles": meta.get("allowed_roles", []),
            "source":        "Enterprise" if meta in enterprise_store.metadata else "User Uploaded"
        })

    return docs


@router.delete("/documents/{doc_title}")
async def delete_document(doc_title: str, authorization: Optional[str] = Header(None)):
    caller = _get_user_from_request(authorization)
    Logger.info(f"Deleting document: {doc_title}")

    # Filter metadata
    initial_len = len(uploaded_store.metadata)
    uploaded_store.metadata = [m for m in uploaded_store.metadata if m["docTitle"] != doc_title]

    if len(uploaded_store.metadata) < initial_len:
        remaining_metadata = list(uploaded_store.metadata)
        uploaded_store.reset()

        for meta in remaining_metadata:
            uploaded_store.add_document(
                title=meta["docTitle"],
                category=meta["category"],
                text=meta["content"],
                version=meta["version"],
                date=meta["date"],
                author=meta["author"],
                tags=meta.get("tags", []),
                allowed_roles=meta.get("allowed_roles", [])
            )
        uploaded_store.save()

        AuditLogger.log(
            action="delete_document",
            user=caller["username"],
            role=caller["role"],
            severity="warning",
            details=f"Document '{doc_title}' removed from vector store."
        )
        return {"message": "Uploaded document deleted successfully."}

    # Check if enterprise (read-only)
    enterprise_exists = any(m["docTitle"] == doc_title for m in enterprise_store.metadata)
    if enterprise_exists:
        raise HTTPException(status_code=403, detail="Enterprise Core policies are read-only and cannot be deleted.")

    raise HTTPException(status_code=404, detail="Document not found.")


# ─── Upload ───────────────────────────────────────────────────────────────────
@router.post("/upload")
async def upload_file(
    file:          UploadFile        = File(...),
    title:         Optional[str]     = Form(None),
    category:      Optional[str]     = Form("General"),
    version:       Optional[str]     = Form("1.0"),
    date:          Optional[str]     = Form(None),
    author:        Optional[str]     = Form("User Upload"),
    tags:          Optional[str]     = Form(""),          # Comma-separated tags
    allowed_roles: Optional[str]     = Form(""),          # Comma-separated roles
    authorization: Optional[str]     = Header(None)
):
    caller     = _get_user_from_request(authorization)
    temp_filename = f"temp-{file.filename}"
    save_path  = os.path.join(Config.UPLOAD_DIR, temp_filename)

    # Parse tags and roles from comma-separated strings
    tag_list  = [t.strip() for t in (tags or "").split(",")  if t.strip()]
    role_list = [r.strip() for r in (allowed_roles or "").split(",") if r.strip()]

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc_title      = title or os.path.splitext(file.filename)[0]
        effective_date = date or "2025-01-01"

        success = process_and_index_file(
            file_path=save_path,
            title=doc_title,
            category=category,
            version=version,
            date=effective_date,
            author=author,
            tags=tag_list,
            allowed_roles=role_list
        )

        if success:
            AuditLogger.log(
                action="upload_document",
                user=caller["username"],
                role=caller["role"],
                severity="info",
                details=f"Document '{doc_title}' uploaded. Tags: {tag_list}. Roles: {role_list}."
            )
            return {"message": "Document uploaded, parsed, and FAISS-indexed successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to parse and index document vectors.")

    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        Logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Speech ───────────────────────────────────────────────────────────────────
@router.post("/speech/transcribe")
async def transcribe_speech(file: UploadFile = File(...)):
    temp_path = os.path.join(Config.UPLOAD_DIR, f"speech-{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        transcript = whisper.transcribe_audio(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"text": transcript}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        Logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speech/synthesize")
async def synthesize_speech(req: TTSRequest):
    output_filename = "tts-output.mp3"
    output_path     = os.path.join(Config.UPLOAD_DIR, output_filename)
    success = tts.text_to_speech(req.text, output_path)
    if success and os.path.exists(output_path):
        return FileResponse(path=output_path, media_type="audio/mpeg", filename=output_filename)
    raise HTTPException(status_code=500, detail="Failed to synthesize speech.")


# ─── Reset ────────────────────────────────────────────────────────────────────
@router.post("/reset")
async def reset_database(authorization: Optional[str] = Header(None)):
    caller = _get_user_from_request(authorization)
    Logger.info("Resetting entire knowledge DB...")

    uploaded_store.reset()
    uploaded_store.save()
    enterprise_store.reset()

    handbook_path = os.path.join(Config.ENTERPRISE_DOCS_DIR, "handbook_2025.txt")
    if os.path.exists(handbook_path):
        with open(handbook_path, "r", encoding="utf-8") as f:
            text = f.read()

        enterprise_store.add_document(
            title="Employee Handbook (Endeavors)",
            category="Compliance & Operations",
            text=text,
            version="2.0",
            date="2025-01-01",
            author="CFO & HR Office"
        )
        enterprise_store.save()

        AuditLogger.log(
            action="reset_database",
            user=caller["username"],
            role=caller["role"],
            severity="high",
            details="Vector database fully reset and rebuilt from handbook_2025.txt."
        )
        return {"message": "FAISS Index successfully rebuilt from handbook_2025.txt and uploads cleared."}
    else:
        raise HTTPException(status_code=404, detail="handbook_2025.txt missing from enterprise directory.")


# ─── Categories / Tags (for frontend filter chips) ───────────────────────────
@router.get("/categories")
async def get_categories():
    """Returns all unique categories and tags currently indexed."""
    all_metadata = enterprise_store.metadata + uploaded_store.metadata
    categories   = list({m.get("category", "General") for m in all_metadata if m.get("category")})
    tags         = list({tag for m in all_metadata for tag in m.get("tags", [])})
    return {"categories": sorted(categories), "tags": sorted(tags)}
