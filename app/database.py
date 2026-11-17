import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.security import hash_password

DB_PATH = os.getenv("DATABASE_PATH", "/app/data/ciberfaro.db")

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea las tablas de la base de datos e inserta usuario demo si no existe."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        domain_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'monitorizado',
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (domain_id) REFERENCES domains (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        user_id INTEGER,
        username TEXT,
        ip_address TEXT,
        details TEXT
    );
    """)

    # Sembrar usuario demo si no existe
    cursor.execute("SELECT id FROM users WHERE username = ?", ("demo",))
    if not cursor.fetchone():
        p_hash, salt = hash_password("Demo1234!")
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
            ("demo", "demo@cyberlearn.com", p_hash, salt, now)
        )
        demo_user_id = cursor.lastrowid
        # Sembrar un dominio demo con alertas simuladas
        cursor.execute(
            "INSERT INTO domains (user_id, domain_name, status, created_at) VALUES (?, ?, ?, ?)",
            (demo_user_id, "lab-ciberfaro.local", "monitorizado", now)
        )
        domain_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO alerts (domain_id, user_id, severity, title, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (domain_id, demo_user_id, "warning", "Certificado TLS autofirmado", "El dominio utiliza un certificado autofirmado no confiable para clientes externos.", now)
        )
        cursor.execute(
            "INSERT INTO alerts (domain_id, user_id, severity, title, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (domain_id, demo_user_id, "info", "Encabezados HSTS ausentes", "Se recomienda configurar el encabezado HTTP Strict-Transport-Security.", now)
        )

    conn.commit()
    conn.close()

def log_event(event_type: str, user_id: Optional[int], username: Optional[str], ip_address: Optional[str], details: str):
    """Registra eventos de seguridad en la tabla audit_logs."""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO audit_logs (timestamp, event_type, user_id, username, ip_address, details) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), event_type, user_id, username, ip_address, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR AUDIT LOG] {e}")
