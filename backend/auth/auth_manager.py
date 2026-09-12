import os
import json
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from backend.utils.logger import Logger

# ─── Constants ───────────────────────────────────────────────────────────────
USERS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'users.json')
SECRET_KEY = os.getenv("JWT_SECRET", "policy_buddy_jwt_secret_key_2025")
TOKEN_EXPIRY_HOURS = 24

VALID_ROLES = ["admin", "hr", "employee"]

# ─── Simple JWT (no external lib dependency) ─────────────────────────────────
import base64
import json as _json

def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64decode(s: str) -> bytes:
    s += '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)

def _create_token(payload: dict) -> str:
    header = _b64encode(_json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body   = _b64encode(_json.dumps(payload).encode())
    sig    = _b64encode(hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"

def _verify_token(token: str) -> Optional[dict]:
    try:
        header, body, sig = token.split(".")
        expected_sig = _b64encode(hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = _json.loads(_b64decode(body))
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            return None
        return payload
    except Exception:
        return None

# ─── Password Hashing ─────────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h    = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return f"{salt}:{h.hex()}"

def _verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":")
        expected = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(expected, bytes.fromhex(h))
    except Exception:
        return False

# ─── User Store ───────────────────────────────────────────────────────────────
def _load_users() -> List[Dict]:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_users(users: List[Dict]):
    os.makedirs(os.path.dirname(os.path.abspath(USERS_FILE)), exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def _ensure_default_admin():
    """Creates default admin user if no users exist."""
    users = _load_users()
    if not any(u["role"] == "admin" for u in users):
        users.append({
            "id": str(uuid.uuid4()),
            "username": "kathirvb24@mail.com",
            "password": _hash_password("vbk241005"),
            "role": "admin",
            "name": "Kathir",
            "email": "kathirvb24@mail.com",
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        })
        _save_users(users)
        Logger.info("Default admin user created (kathirvb24@mail.com / vbk241005).")

# Ensure admin exists on import
_ensure_default_admin()

# ─── Public API ───────────────────────────────────────────────────────────────
class AuthManager:

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict]:
        """Verifies credentials and returns a JWT token + user info dict on success."""
        users = _load_users()
        user  = next((u for u in users if u["username"] == username and u.get("active", True)), None)
        if not user or not _verify_password(password, user["password"]):
            return None

        exp = (datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)).timestamp()
        token = _create_token({
            "sub":  user["id"],
            "username": user["username"],
            "role": user["role"],
            "name": user["name"],
            "exp":  exp
        })
        return {
            "token": token,
            "user": {
                "id":       user["id"],
                "username": user["username"],
                "role":     user["role"],
                "name":     user["name"],
                "email":    user.get("email", ""),
            }
        }

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verifies a JWT token and returns the payload, or None if invalid/expired."""
        return _verify_token(token)

    @staticmethod
    def get_user_from_token(token: str) -> Optional[Dict]:
        """Returns user dict from a valid token."""
        payload = _verify_token(token)
        if not payload:
            return None
        return {
            "id":       payload.get("sub"),
            "username": payload.get("username"),
            "role":     payload.get("role", "employee"),
            "name":     payload.get("name", ""),
        }

    @staticmethod
    def list_users() -> List[Dict]:
        """Returns all users (without password hashes)."""
        users = _load_users()
        return [
            {
                "id":         u["id"],
                "username":   u["username"],
                "role":       u["role"],
                "name":       u["name"],
                "email":      u.get("email", ""),
                "created_at": u.get("created_at", ""),
                "active":     u.get("active", True)
            }
            for u in users
        ]

    @staticmethod
    def create_user(username: str, password: str, role: str, name: str, email: str = "") -> Dict:
        """Creates a new user. Returns the created user dict."""
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")

        users = _load_users()
        if any(u["username"] == username for u in users):
            raise ValueError(f"Username '{username}' already exists.")

        new_user = {
            "id":         str(uuid.uuid4()),
            "username":   username,
            "password":   _hash_password(password),
            "role":       role,
            "name":       name,
            "email":      email,
            "created_at": datetime.utcnow().isoformat(),
            "active":     True
        }
        users.append(new_user)
        _save_users(users)
        Logger.info(f"User '{username}' created with role '{role}'.")
        return {k: v for k, v in new_user.items() if k != "password"}

    @staticmethod
    def delete_user(username: str) -> bool:
        """Deletes a user. Returns True if deleted, False if not found."""
        users = _load_users()
        new_users = [u for u in users if u["username"] != username]
        if len(new_users) == len(users):
            return False
        _save_users(new_users)
        Logger.info(f"User '{username}' deleted.")
        return True

    @staticmethod
    def change_password(username: str, new_password: str) -> bool:
        """Changes a user's password. Returns True on success."""
        users = _load_users()
        for user in users:
            if user["username"] == username:
                user["password"] = _hash_password(new_password)
                _save_users(users)
                Logger.info(f"Password changed for user '{username}'.")
                return True
        return False

    @staticmethod
    def update_role(username: str, new_role: str) -> bool:
        """Updates a user's role. Returns True on success."""
        if new_role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{new_role}'.")
        users = _load_users()
        for user in users:
            if user["username"] == username:
                user["role"] = new_role
                _save_users(users)
                Logger.info(f"Role updated for user '{username}' → '{new_role}'.")
                return True
        return False

    @staticmethod
    def get_valid_roles() -> List[str]:
        return VALID_ROLES
