import os
import shutil
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from backend.config import Config
from backend.graph.graph import run_workflow
from backend.rag.retriever import enterprise_store, uploaded_store
from backend.rag.document_loader import load_document
from backend.upload.upload_handler import save_uploaded_file
from backend.upload.process_uploaded_pdf import process_and_index_file
from backend.speech import whisper, tts
from backend.utils.logger import Logger

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = None
    history: Optional[list] = None
    session_id: Optional[str] = None

class TTSRequest(BaseModel):
    text: str

@router.get("/models")
async def get_models():
    return [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gpt-4.1-nano", "name": "GPT 4.1 Nano"},
        {"id": "gpt-4o-mini-tts", "name": "GPT 4o Mini TTS"},
        {"id": "whisper-1", "name": "Whisper 1 (Audio)"},
        {"id": "nova-micro", "name": "Nova Micro"}
    ]

@router.post("/query")
async def process_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        response = run_workflow(req.query, req.model, req.history, req.session_id)
        return response
    except Exception as e:
        Logger.error(f"Error processing graph workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def get_documents():
    # Return lists of all active documents in metadata
    docs = []
    # Deduplicate by document title
    seen = set()
    
    # Combined metadata
    all_metadata = enterprise_store.metadata + uploaded_store.metadata
    for meta in all_metadata:
        title = meta['docTitle']
        if title not in seen:
            seen.add(title)
            docs.append({
                "id": meta.get('id', title),
                "title": title,
                "category": meta.get('category', 'General'),
                "version": meta.get('version', '1.0'),
                "date": meta.get('date', 'Unknown'),
                "author": meta.get('author', 'Unknown'),
                "source": "Enterprise" if meta in enterprise_store.metadata else "User Uploaded"
            })
    return docs

@router.delete("/documents/{doc_title}")
async def delete_document(doc_title: str):
    Logger.info(f"Deleting document: {doc_title}")
    
    # Filter metadata
    initial_len = len(uploaded_store.metadata)
    uploaded_store.metadata = [m for m in uploaded_store.metadata if m['docTitle'] != doc_title]
    
    if len(uploaded_store.metadata) < initial_len:
        # Re-build the FAISS index for uploaded index (removes references)
        # To keep it simple, we reset the index and re-add remaining documents
        remaining_metadata = list(uploaded_store.metadata)
        uploaded_store.reset()
        
        for meta in remaining_metadata:
            uploaded_store.add_document(
                title=meta['docTitle'],
                category=meta['category'],
                text=meta['content'],
                version=meta['version'],
                date=meta['date'],
                author=meta['author']
            )
        uploaded_store.save()
        return {"message": "Uploaded document deleted successfully."}
        
    # Check if in enterprise docs (enterprise is read-only)
    enterprise_exists = any(m['docTitle'] == doc_title for m in enterprise_store.metadata)
    if enterprise_exists:
        raise HTTPException(status_code=403, detail="Enterprise Core policies are read-only and cannot be deleted.")
        
    raise HTTPException(status_code=404, detail="Document not found.")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("General"),
    version: Optional[str] = Form("1.0"),
    date: Optional[str] = Form(None),
    author: Optional[str] = Form("User Upload")
):
    temp_filename = f"temp-{file.filename}"
    save_path = os.path.join(Config.UPLOAD_DIR, temp_filename)
    
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc_title = title or os.path.splitext(file.filename)[0]
        effective_date = date or "2025-01-01"
        
        success = process_and_index_file(
            file_path=save_path,
            title=doc_title,
            category=category,
            version=version,
            date=effective_date,
            author=author
        )
        
        if success:
            return {"message": "Document uploaded, parsed, and FAISS-indexed successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to parse and index document vectors.")
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        Logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    output_path = os.path.join(Config.UPLOAD_DIR, output_filename)
    
    success = tts.text_to_speech(req.text, output_path)
    
    if success and os.path.exists(output_path):
        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename=output_filename
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech.")

@router.post("/reset")
async def reset_database():
    Logger.info("Resetting entire knowledge DB...")
    
    # 1. Reset uploaded index
    uploaded_store.reset()
    uploaded_store.save()
    
    # 2. Re-index handbook_2025 in enterprise index
    enterprise_store.reset()
    
    handbook_path = os.path.join(Config.ENTERPRISE_DOCS_DIR, 'handbook_2025.txt')
    if os.path.exists(handbook_path):
        with open(handbook_path, 'r', encoding='utf-8') as f:
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
        return {"message": "FAISS Index successfully rebuilt from handbook_2025.txt and uploads cleared."}
    else:
        raise HTTPException(status_code=404, detail="handbook_2025.txt missing from enterprise directory.")
