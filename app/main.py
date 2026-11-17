import os
import re
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.database import init_db, get_db_connection, log_event
from app.security import (
    hash_password,
    verify_password,
    create_session_token,
    verify_session_token
)

# Configuración de logs estructurados (para observabilidad con docker compose logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("ciberfaro.web")

app = FastAPI(
    title="CiberFaro LAB - Plataforma de Ciberseguridad",
    description="Aplicación web educativa para Puesta en Producción Segura (PPS) y Hacking Ético",
    version="1.0.0"
)

# Inicializar base de datos al arrancar
@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Base de datos SQLite inicializada correctamente en %s", os.getenv("DATABASE_PATH", "/app/data/ciberfaro.db"))

# Modelos Pydantic para validación estricta
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class DomainRequest(BaseModel):
    domain_name: str

# Helper para obtener usuario actual desde cookie o cabecera Authorization
def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    data = verify_session_token(token)
    if not data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o caducada")

    conn = get_db_connection()
    user = conn.execute("SELECT id, username, email FROM users WHERE id = ?", (data["user_id"],)).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

    return dict(user)

# ============================================================
# ENDPOINTS PRINCIPALES Y OBSERVABILIDAD
# ============================================================

@app.get("/health", tags=["Observabilidad"])
def health_check():
    """Endpoint de comprobación de salud del servicio (requerido por la guía de laboratorio)."""
    return {
        "status": "ok",
        "service": "CiberFaro LAB",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# ============================================================
# AUTENTICACIÓN Y SESIONES
# ============================================================

@app.post("/api/register", tags=["Autenticación"])
def register(req: RegisterRequest, request: Request):
    username = req.username.strip()
    if len(username) < 3 or len(username) > 30 or not re.match(r"^[a-zA-Z0-9_\-]+$", username):
        raise HTTPException(status_code=400, detail="Nombre de usuario inválido (3-30 caracteres alfanuméricos)")

    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    conn = get_db_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
        (username.lower(), req.email.lower())
    ).fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="El usuario o correo electrónico ya está registrado")

    p_hash, salt = hash_password(req.password)
    now = datetime.utcnow().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, req.email.lower(), p_hash, salt, now)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "unknown"
    log_event("USER_REGISTER", user_id, username, client_ip, "Registro de nueva cuenta exitoso")
    logger.info("AUDIT: Usuario registrado id=%s username='%s' desde ip=%s", user_id, username, client_ip)

    return {"success": True, "message": "Cuenta creada correctamente"}

@app.post("/api/login", tags=["Autenticación"])
def login(req: LoginRequest, request: Request, response: Response):
    identifier = req.username_or_email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"

    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username, email, password_hash, salt FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
        (identifier, identifier)
    ).fetchone()
    conn.close()

    if not user or not verify_password(req.password, user["password_hash"], user["salt"]):
        log_event("LOGIN_FAILED", None, identifier, client_ip, "Intento de inicio de sesión fallido")
        logger.warning("AUDIT: Fallo de login para '%s' desde ip=%s", identifier, client_ip)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = create_session_token(user["id"], user["username"])
    # Cookie de sesión HTTPOnly protegida
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400
    )

    log_event("LOGIN_SUCCESS", user["id"], user["username"], client_ip, "Inicio de sesión correcto")
    logger.info("AUDIT: Login exitoso id=%s username='%s' desde ip=%s", user["id"], user["username"], client_ip)

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }

@app.post("/api/logout", tags=["Autenticación"])
def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie(key="session_token")
    log_event("LOGOUT", user["id"], user["username"], None, "Cierre de sesión")
    logger.info("AUDIT: Cierre de sesión id=%s username='%s'", user["id"], user["username"])
    return {"success": True, "message": "Sesión cerrada"}

@app.get("/api/me", tags=["Autenticación"])
def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}

# ============================================================
# ALTA DE DOMINIO Y ALERTAS SIMULADAS (Sesión 3)
# ============================================================

DOMAIN_REGEX = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.(?:[A-Za-z]{2,}|(?:[A-Za-z0-9-]{1,63}\.[A-Za-z]{2,}))(?::[0-9]{1,5})?$"

@app.get("/api/domains", tags=["Dominios"])
def list_domains(user: dict = Depends(get_current_user)):
    """Lista exclusivamente los dominios pertenecientes al usuario autenticado (aislamiento de usuarios)."""
    conn = get_db_connection()
    domains = conn.execute(
        "SELECT id, domain_name, status, created_at FROM domains WHERE user_id = ? ORDER BY id DESC",
        (user["id"],)
    ).fetchall()
    conn.close()
    return {"domains": [dict(d) for d in domains]}

@app.post("/api/domains", tags=["Dominios"])
def add_domain(req: DomainRequest, request: Request, user: dict = Depends(get_current_user)):
    """Alta de dominio para monitorización con validación estricta y generación de alertas simuladas."""
    raw_domain = req.domain_name.strip().lower()

    # Validación de formato seguro
    if not re.match(DOMAIN_REGEX, raw_domain):
        raise HTTPException(
            status_code=400,
            detail="Formato de dominio inválido. Ejemplo: midominio.es o api.sitio.com"
        )

    conn = get_db_connection()
    # Verificar si el usuario ya tiene este dominio
    existing = conn.execute(
        "SELECT id FROM domains WHERE user_id = ? AND domain_name = ?",
        (user["id"], raw_domain)
    ).fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Este dominio ya está dado de alta en tu panel")

    now = datetime.utcnow().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO domains (user_id, domain_name, status, created_at) VALUES (?, ?, ?, ?)",
        (user["id"], raw_domain, "monitorizado", now)
    )
    domain_id = cursor.lastrowid

    # Simulación didáctica de alertas de ciberseguridad asociadas al dominio
    simulated_alerts = [
        ("warning", f"Encabezados de seguridad ausentes en {raw_domain}", "Faltan Content-Security-Policy y Permissions-Policy."),
        ("info", f"Registro DNS verificado para {raw_domain}", "El registro A y CNAME apuntan a servidores seguros.")
    ]
    if "admin" in raw_domain or "test" in raw_domain:
        simulated_alerts.append(
            ("danger", f"Subdominio sensible detectado: {raw_domain}", "Posible exposición de interfaz de administración o entorno de pruebas.")
        )

    for sev, title, desc in simulated_alerts:
        cursor.execute(
            "INSERT INTO alerts (domain_id, user_id, severity, title, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (domain_id, user["id"], sev, title, desc, now)
        )

    conn.commit()
    conn.close()

    client_ip = request.client.host if request.client else "unknown"
    log_event("DOMAIN_ADD", user["id"], user["username"], client_ip, f"Alta de dominio: {raw_domain}")
    logger.info("AUDIT: Alta de dominio id=%s usuario='%s' dominio='%s'", domain_id, user["username"], raw_domain)

    return {"success": True, "message": f"Dominio {raw_domain} dado de alta y monitorizado", "domain_id": domain_id}

@app.delete("/api/domains/{domain_id}", tags=["Dominios"])
def delete_domain(domain_id: int, user: dict = Depends(get_current_user)):
    """Elimina un dominio asegurando aislamiento: solo el propietario puede borrarlo."""
    conn = get_db_connection()
    domain = conn.execute(
        "SELECT id, domain_name FROM domains WHERE id = ? AND user_id = ?",
        (domain_id, user["id"])
    ).fetchone()

    if not domain:
        conn.close()
        raise HTTPException(status_code=404, detail="Dominio no encontrado o no pertenece a tu cuenta")

    conn.execute("DELETE FROM alerts WHERE domain_id = ?", (domain_id,))
    conn.execute("DELETE FROM domains WHERE id = ?", (domain_id,))
    conn.commit()
    conn.close()

    log_event("DOMAIN_DELETE", user["id"], user["username"], None, f"Baja de dominio: {domain['domain_name']}")
    return {"success": True, "message": "Dominio eliminado"}

@app.get("/api/alerts", tags=["Alertas"])
def list_alerts(user: dict = Depends(get_current_user)):
    """Obtiene las alertas simuladas de los dominios del usuario autenticado."""
    conn = get_db_connection()
    alerts = conn.execute(
        """SELECT a.id, a.domain_id, d.domain_name, a.severity, a.title, a.description, a.created_at
           FROM alerts a
           JOIN domains d ON a.domain_id = d.id
           WHERE a.user_id = ?
           ORDER BY a.id DESC""",
        (user["id"],)
    ).fetchall()
    conn.close()
    return {"alerts": [dict(a) for a in alerts]}

@app.get("/api/audit-logs", tags=["Auditoría"])
def list_audit_logs(user: dict = Depends(get_current_user)):
    """Obtiene registros de auditoría asociados al usuario."""
    conn = get_db_connection()
    logs = conn.execute(
        "SELECT id, timestamp, event_type, ip_address, details FROM audit_logs WHERE user_id = ? ORDER BY id DESC LIMIT 50",
        (user["id"],)
    ).fetchall()
    conn.close()
    return {"logs": [dict(l) for l in logs]}

# ============================================================
# ARCHIVOS ESTÁTICOS Y VISTAS HTML
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Montar carpetas estáticas
if os.path.exists(os.path.join(BASE_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(BASE_DIR, "css")), name="css")
if os.path.exists(os.path.join(BASE_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(BASE_DIR, "js")), name="js")

@app.get("/", include_in_schema=False)
def serve_root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/{page_name}.html", include_in_schema=False)
def serve_html(page_name: str):
    file_path = os.path.join(BASE_DIR, f"{page_name}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Página no encontrada")
