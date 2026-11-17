import os
import pytest
from fastapi.testclient import TestClient

# Configurar entorno de pruebas
os.environ["SESSION_SECRET"] = "test_secret_for_pytest_environment_only_12345678"
os.environ["DATABASE_PATH"] = "/tmp/ciberfaro_test.db"

# Limpiar BD anterior de test
if os.path.exists("/tmp/ciberfaro_test.db"):
    os.remove("/tmp/ciberfaro_test.db")

from app.main import app
from app.database import init_db

init_db()
client = TestClient(app)

def test_health_endpoint():
    """Sesión 1: Verifica el endpoint de salud /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data

def test_user_registration_and_login():
    """Sesión 3: Registro y acceso de usuario."""
    # Registro
    reg_resp = client.post("/api/register", json={
        "username": "usuario_test",
        "email": "test@dominio.com",
        "password": "Password123!"
    })
    assert reg_resp.status_code == 200
    assert reg_resp.json()["success"] is True

    # Login
    login_resp = client.post("/api/login", json={
        "username_or_email": "usuario_test",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()
    assert "session_token" in login_resp.cookies

def test_domain_validation_rejects_malicious_inputs():
    """Sesión 3: Pruebas con entradas inválidas (sin inyecciones permitidas)."""
    # Login como demo
    login_resp = client.post("/api/login", json={
        "username_or_email": "demo",
        "password": "Demo1234!"
    })
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Intentos de inyección y dominios inválidos
    invalid_domains = [
        "dominio; rm -rf /",
        "<script>alert(1)</script>",
        "dominio con espacios .es",
        "-dominioinvalido.com",
        "dominio..doblepunto.com"
    ]

    for inv in invalid_domains:
        resp = client.post("/api/domains", json={"domain_name": inv}, headers=headers)
        assert resp.status_code == 400, f"Debería rechazar '{inv}' pero devolvió {resp.status_code}"

def test_reto_opcional_user_isolation():
    """Reto Opcional: Prueba automatizada de aislamiento estricto entre usuarios."""
    # 1. Registrar y autenticar Usuario A
    client.post("/api/register", json={
        "username": "alice",
        "email": "alice@empresa.es",
        "password": "AliceSecret123!"
    })
    token_a = client.post("/api/login", json={
        "username_or_email": "alice",
        "password": "AliceSecret123!"
    }).json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Alice da de alta su dominio confidencial
    add_resp = client.post("/api/domains", json={"domain_name": "confidencial-alice.com"}, headers=headers_a)
    assert add_resp.status_code == 200
    domain_id_alice = add_resp.json()["domain_id"]

    # 3. Registrar y autenticar Usuario B (Bob)
    client.post("/api/register", json={
        "username": "bob",
        "email": "bob@atacante.es",
        "password": "BobSecret123!"
    })
    token_b = client.post("/api/login", json={
        "username_or_email": "bob",
        "password": "BobSecret123!"
    }).json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. Bob consulta la lista de dominios: NO debe ver el dominio de Alice
    domains_b = client.get("/api/domains", headers=headers_b).json()["domains"]
    assert not any(d["id"] == domain_id_alice for d in domains_b), "Fallo de aislamiento: Bob puede ver el dominio de Alice"

    # 5. Bob intenta eliminar el dominio de Alice (IDOR): debe ser rechazado con 404
    delete_resp = client.delete(f"/api/domains/{domain_id_alice}", headers=headers_b)
    assert delete_resp.status_code == 404, "Fallo de aislamiento: Bob pudo eliminar el dominio de Alice"
