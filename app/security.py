import os
import hashlib
import secrets
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev_insecure_fallback_secret_32_bytes_min")
serializer = URLSafeTimedSerializer(SESSION_SECRET)

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Genera hash de contraseña con PBKDF2-HMAC-SHA256 y salt de 16 bytes."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100_000
    )
    return key.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifica la contraseña contra el hash almacenado."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, password_hash)

def create_session_token(user_id: int, username: str) -> str:
    """Crea un token de sesión firmado."""
    return serializer.dumps({"user_id": user_id, "username": username})

def verify_session_token(token: str, max_age: int = 86400) -> Optional[dict]:
    """Verifica y decodifica un token de sesión (validez por defecto: 24 horas)."""
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except (BadSignature, SignatureExpired):
        return None
