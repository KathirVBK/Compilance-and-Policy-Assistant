from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from backend.auth.auth_manager import AuthManager
from backend.utils.audit_logger import AuditLogger
from backend.utils.logger import Logger

auth_router = APIRouter()


# ─── Request/Response Models ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    email: str = ""

class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str


# ─── Helper: extract Bearer token ─────────────────────────────────────────────
def _get_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[len("Bearer "):]


# ─── Endpoints ────────────────────────────────────────────────────────────────
@auth_router.post("/login")
async def login(req: LoginRequest):
    result = AuthManager.authenticate(req.username, req.password)
    if not result:
        AuditLogger.log(
            action="login_failed",
            user=req.username,
            severity="warning",
            details=f"Invalid credentials for username '{req.username}'"
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    AuditLogger.log(
        action="login",
        user=result["user"]["username"],
        role=result["user"]["role"],
        severity="info",
        details=f"User '{result['user']['username']}' logged in successfully."
    )
    Logger.info(f"User '{req.username}' authenticated successfully.")
    return result


@auth_router.post("/register")
async def register(req: RegisterRequest):
    try:
        user = AuthManager.create_user(req.username, req.password, "employee", req.name, req.email)
        AuditLogger.log(
            action="register",
            user=req.username,
            role="employee",
            severity="info",
            details=f"User '{req.username}' registered successfully."
        )
        return {"message": "User registered successfully", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    token = _get_token(authorization)
    user = AuthManager.get_user_from_token(token) if token else None
    username = user["username"] if user else "unknown"
    AuditLogger.log(action="logout", user=username, severity="info", details=f"User '{username}' logged out.")
    return {"message": "Logged out successfully."}


@auth_router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    token = _get_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")

    user = AuthManager.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token expired or invalid.")
    return user


@auth_router.post("/change-password")
async def change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    token = _get_token(authorization)
    caller = AuthManager.get_user_from_token(token) if token else None

    if not caller:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # Only admins can change other users' passwords; self-change always allowed
    if caller["username"] != req.username and caller["role"] != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions to change another user's password.")

    success = AuthManager.change_password(req.username, req.new_password)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")

    AuditLogger.log(
        action="change_password",
        user=caller["username"],
        role=caller["role"],
        severity="warning",
        details=f"Password changed for user '{req.username}'."
    )
    return {"message": f"Password updated for '{req.username}'."}


@auth_router.get("/roles")
async def get_roles():
    """Returns the list of valid roles — used by frontend dropdowns."""
    return {"roles": AuthManager.get_valid_roles()}
