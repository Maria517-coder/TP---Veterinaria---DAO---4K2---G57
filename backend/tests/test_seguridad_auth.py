"""Tests de autenticación, autorización y protección de endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.core.dependencias import obtener_usuario_actual, requiere_admin
from app.main import app
from app.models.usuario import RolUsuario
from app.schemas.auth import UsuarioCrear
from app.services.usuario_service import UsuarioService


@pytest.fixture()
def client_sin_auth(db):
    """Cliente sin override de autenticación: prueba el comportamiento real."""
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    app.dependency_overrides.pop(requiere_admin, None)
    with TestClient(app) as cliente:
        yield cliente
    # conftest autouse restaurará en su teardown; por seguridad dejamos limpio aquí


def _crear_usuario(db, nombre_usuario: str, contrasena: str, rol: RolUsuario, activo: bool = True):
    service = UsuarioService(db)
    usuario = service.crear(UsuarioCrear(nombre_usuario=nombre_usuario, contrasena=contrasena, rol=rol))
    if not activo:
        usuario.activo = False
        db.commit()
        db.refresh(usuario)
    return usuario


def _login(client_sin_auth, usuario: str, contrasena: str):
    return client_sin_auth.post("/api/auth/login", json={"usuario": usuario, "contrasena": contrasena})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_correcto_devuelve_token_y_rol(db, client_sin_auth) -> None:
    _crear_usuario(db, "ana", "secreta123", RolUsuario.VETERINARIO)
    r = _login(client_sin_auth, "ana", "secreta123")
    assert r.status_code == 200
    cuerpo = r.json()
    assert "token" in cuerpo
    assert cuerpo["rol"] == "VETERINARIO"
    assert "contrasena_hash" not in cuerpo
    assert "contrasena" not in cuerpo


def test_login_incorrecto_mismo_mensaje_para_usuario_y_contrasena(db, client_sin_auth) -> None:
    _crear_usuario(db, "ana", "secreta123", RolUsuario.VETERINARIO)
    r_usuario = _login(client_sin_auth, "no-existe", "secreta123")
    r_pass = _login(client_sin_auth, "ana", "mala")
    assert r_usuario.status_code == 401
    assert r_pass.status_code == 401
    assert r_usuario.json()["detalle"] == "Credenciales inválidas"
    assert r_pass.json()["detalle"] == "Credenciales inválidas"


def test_usuario_inactivo_no_entra(db, client_sin_auth) -> None:
    _crear_usuario(db, "ana", "secreta123", RolUsuario.VETERINARIO, activo=False)
    r = _login(client_sin_auth, "ana", "secreta123")
    assert r.status_code == 401
    assert r.json()["detalle"] == "Credenciales inválidas"


def test_sin_token_da_401_en_un_endpoint_de_cada_router(db, client_sin_auth) -> None:
    endpoints = [
        ("GET", "/api/clientes"),
        ("GET", "/api/mascotas"),
        ("GET", "/api/clinicas"),
        ("GET", "/api/tipos-muestra"),
        ("GET", "/api/veterinarios/1/agenda"),
        ("GET", "/api/consultas"),
        ("GET", "/api/muestras"),
        ("GET", "/api/contenedores"),
        ("GET", "/api/remitos"),
        ("GET", "/api/reportes/facturacion"),
        ("GET", "/api/auth/yo"),
        ("POST", "/api/usuarios"),
    ]
    for metodo, ruta in endpoints:
        r = client_sin_auth.request(metodo, ruta)
        assert r.status_code == 401, f"{metodo} {ruta} devolvió {r.status_code}: {r.text}"


def test_health_y_login_andan_sin_token(client_sin_auth) -> None:
    r_health = client_sin_auth.get("/api/health")
    assert r_health.status_code == 200
    r_login = client_sin_auth.post("/api/auth/login", json={"usuario": "x", "contrasena": "y"})
    assert r_login.status_code == 401  # responde, no bloqueado por falta de token
    assert r_login.json()["detalle"] == "Credenciales inválidas"


def test_veterinario_no_puede_crear_clinica_ni_veterinario_y_admin_si(db, client_sin_auth) -> None:
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    _crear_usuario(db, "vet1", "vetpass", RolUsuario.VETERINARIO)

    token_admin = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    token_vet = _login(client_sin_auth, "vet1", "vetpass").json()["token"]

    r_vet_clinica = client_sin_auth.post(
        "/api/red/clinicas", json={"nombre": "Clinica Vet"}, headers=_auth_header(token_vet)
    )
    assert r_vet_clinica.status_code == 403

    r_admin_clinica = client_sin_auth.post(
        "/api/red/clinicas", json={"nombre": "Clinica Admin"}, headers=_auth_header(token_admin)
    )
    assert r_admin_clinica.status_code == 201
    clinica_id = r_admin_clinica.json()["id"]

    r_vet_vet = client_sin_auth.post(
        f"/api/clinicas/{clinica_id}/veterinarios",
        json={"matricula": "VET-1", "nombre": "Dr Vet"},
        headers=_auth_header(token_vet),
    )
    assert r_vet_vet.status_code == 403

    r_admin_vet = client_sin_auth.post(
        f"/api/clinicas/{clinica_id}/veterinarios",
        json={"matricula": "VET-1", "nombre": "Dr Vet"},
        headers=_auth_header(token_admin),
    )
    assert r_admin_vet.status_code == 201


def test_respuesta_nunca_incluye_hash(db, client_sin_auth) -> None:
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    token_admin = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    headers = _auth_header(token_admin)

    r_yo = client_sin_auth.get("/api/auth/yo", headers=headers)
    assert r_yo.status_code == 200
    assert "contrasena_hash" not in r_yo.text

    r_crear = client_sin_auth.post(
        "/api/usuarios",
        json={"nombre_usuario": "otro", "contrasena": "pass1234", "rol": "VETERINARIO"},
        headers=headers,
    )
    assert r_crear.status_code == 201
    cuerpo_crear = r_crear.json()
    assert "contrasena_hash" not in cuerpo_crear
    assert "contrasena" not in cuerpo_crear
    assert "pass1234" not in r_crear.text
