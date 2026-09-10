from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from backend.auth.auth_manager import AuthManager
from backend.utils.audit_logger import AuditLogger
from backend.rag.retriever import enterprise_store, uploaded_store
from backend.utils.logger import Logger

admin_router = APIRouter()


# ─── Request Models ───────────────────────────────────────────────────────────
class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str
    name: str
    email: Optional[str] = ""

class UpdateRoleRequest(BaseModel):
    role: str

class UpdateDocRolesRequest(BaseModel):
    allowed_roles: List[str]  # empty list = public

class UpdateDocTagsRequest(BaseModel):
    tags: List[str]


# ─── Auth guard ───────────────────────────────────────────────────────────────
def _require_admin(authorization: Optional[str]) -> dict:
    """Extracts and validates the token; raises 403 if not admin."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header.")
    token = authorization[len("Bearer "):]
    user = AuthManager.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token expired or invalid.")
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


# ─── User Management ──────────────────────────────────────────────────────────
@admin_router.get("/users")
async def list_users(authorization: Optional[str] = Header(None)):
    caller = _require_admin(authorization)
    return {"users": AuthManager.list_users()}


@admin_router.post("/users")
async def create_user(req: CreateUserRequest, authorization: Optional[str] = Header(None)):
    caller = _require_admin(authorization)
    try:
        user = AuthManager.create_user(req.username, req.password, req.role, req.name, req.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    AuditLogger.log(
        action="create_user",
        user=caller["username"],
        role=caller["role"],
        severity="warning",
        details=f"Admin created user '{req.username}' with role '{req.role}'."
    )
    return {"message": f"User '{req.username}' created successfully.", "user": user}


@admin_router.delete("/users/{username}")
async def delete_user(username: str, authorization: Optional[str] = Header(None)):
    caller = _require_admin(authorization)
    if username == caller["username"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account.")

    success = AuthManager.delete_user(username)
    if not success:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found.")

    AuditLogger.log(
        action="delete_user",
        user=caller["username"],
        role=caller["role"],
        severity="high",
        details=f"Admin deleted user '{username}'."
    )
    return {"message": f"User '{username}' deleted."}


@admin_router.patch("/users/{username}/role")
async def update_user_role(username: str, req: UpdateRoleRequest, authorization: Optional[str] = Header(None)):
    caller = _require_admin(authorization)
    try:
        success = AuthManager.update_role(username, req.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not success:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found.")

    AuditLogger.log(
        action="update_role",
        user=caller["username"],
        role=caller["role"],
        severity="warning",
        details=f"Role updated for '{username}' → '{req.role}'."
    )
    return {"message": f"Role for '{username}' updated to '{req.role}'."}


# ─── Audit Log ────────────────────────────────────────────────────────────────
@admin_router.get("/audit-log")
async def get_audit_log(
    limit: int = 200,
    severity: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    _require_admin(authorization)
    entries = AuditLogger.get_entries(limit=limit, severity_filter=severity)
    return {"entries": entries, "total": len(entries)}


@admin_router.delete("/audit-log")
async def clear_audit_log(authorization: Optional[str] = Header(None)):
    caller = _require_admin(authorization)
    AuditLogger.clear()
    AuditLogger.log(
        action="clear_audit_log",
        user=caller["username"],
        role=caller["role"],
        severity="high",
        details="Audit log cleared by admin."
    )
    return {"message": "Audit log cleared."}


# ─── Vector DB Stats ─────────────────────────────────────────────────────────
@admin_router.get("/stats")
async def get_stats(authorization: Optional[str] = Header(None)):
    _require_admin(authorization)

    # Enterprise store stats
    ent_docs  = list({m["docTitle"] for m in enterprise_store.metadata})
    ent_cats  = list({m.get("category", "General") for m in enterprise_store.metadata})

    # Uploaded store stats
    upl_docs  = list({m["docTitle"] for m in uploaded_store.metadata})
    upl_cats  = list({m.get("category", "General") for m in uploaded_store.metadata})

    # Role-restricted docs
    restricted = [
        {
            "title":         m["docTitle"],
            "allowed_roles": m.get("allowed_roles", []),
            "tags":          m.get("tags", [])
        }
        for m in (enterprise_store.metadata + uploaded_store.metadata)
        if m.get("allowed_roles")
    ]
    # Deduplicate by title
    seen = set()
    restricted_unique = []
    for r in restricted:
        if r["title"] not in seen:
            seen.add(r["title"])
            restricted_unique.append(r)

    return {
        "enterprise": {
            "chunk_count": len(enterprise_store.metadata),
            "document_count": len(ent_docs),
            "documents": ent_docs,
            "categories": ent_cats
        },
        "uploaded": {
            "chunk_count": len(uploaded_store.metadata),
            "document_count": len(upl_docs),
            "documents": upl_docs,
            "categories": upl_cats
        },
        "total_chunks": len(enterprise_store.metadata) + len(uploaded_store.metadata),
        "role_restricted_docs": restricted_unique
    }


# ─── Document Role & Tag Management ──────────────────────────────────────────
@admin_router.patch("/documents/{doc_title}/roles")
async def update_doc_roles(
    doc_title: str,
    req: UpdateDocRolesRequest,
    authorization: Optional[str] = Header(None)
):
    caller = _require_admin(authorization)

    updated = 0
    for store in [enterprise_store, uploaded_store]:
        for chunk in store.metadata:
            if chunk["docTitle"] == doc_title:
                chunk["allowed_roles"] = req.allowed_roles
                updated += 1
        if updated:
            store.save()
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Document '{doc_title}' not found.")

    AuditLogger.log(
        action="update_doc_roles",
        user=caller["username"],
        role=caller["role"],
        severity="warning",
        details=f"Role restrictions for '{doc_title}' set to: {req.allowed_roles}"
    )
    return {"message": f"Roles updated for '{doc_title}'.", "allowed_roles": req.allowed_roles}


@admin_router.patch("/documents/{doc_title}/tags")
async def update_doc_tags(
    doc_title: str,
    req: UpdateDocTagsRequest,
    authorization: Optional[str] = Header(None)
):
    caller = _require_admin(authorization)

    updated = 0
    for store in [enterprise_store, uploaded_store]:
        for chunk in store.metadata:
            if chunk["docTitle"] == doc_title:
                chunk["tags"] = req.tags
                updated += 1
        if updated:
            store.save()
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Document '{doc_title}' not found.")

    AuditLogger.log(
        action="update_doc_tags",
        user=caller["username"],
        role=caller["role"],
        severity="info",
        details=f"Tags for '{doc_title}' set to: {req.tags}"
    )
    return {"message": f"Tags updated for '{doc_title}'.", "tags": req.tags}
