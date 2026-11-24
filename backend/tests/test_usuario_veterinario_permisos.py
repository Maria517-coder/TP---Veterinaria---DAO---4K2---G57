"""Tests de vinculación Usuario-Veterinario y permisos por rol."""
import pytest
from fastapi.testclient import TestClient

from app.core.dependencias import obtener_usuario_actual, requiere_admin
from app.main import app
from app.models.usuario import RolUsuario
from app.schemas.auth import UsuarioCrear
from app.services.usuario_service import UsuarioService


@pytest.fixture()
def client_sin_auth(db):
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    app.dependency_overrides.pop(requiere_admin, None)
    with TestClient(app) as cliente:
        yield cliente


def _crear_usuario(db, nombre_usuario, contrasena, rol, veterinario_id=None, activo=True):
    service = UsuarioService(db)
    usuario = service.crear(
        UsuarioCrear(
            nombre_usuario=nombre_usuario,
            contrasena=contrasena,
            rol=rol,
            veterinario_id=veterinario_id,
        )
    )
    if not activo:
        usuario.activo = False
        db.commit()
        db.refresh(usuario)
    return usuario


def _login(client_sin_auth, usuario, contrasena):
    return client_sin_auth.post("/api/auth/login", json={"usuario": usuario, "contrasena": contrasena})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _crear_clinica(client_sin_auth, headers, nombre="Clinica Test"):
    r = client_sin_auth.post("/api/red/clinicas", json={"nombre": nombre}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _crear_veterinario(client_sin_auth, headers, clinica_id, matricula="MAT-1", nombre="Dra. Test", acceso=None):
    body = {"matricula": matricula, "nombre": nombre}
    if acceso is not None:
        body["acceso"] = acceso
    r = client_sin_auth.post(f"/api/clinicas/{clinica_id}/veterinarios", json=body, headers=headers)
    return r


def _setup_admin_vet(db, client_sin_auth):
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    token_admin = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    h_admin = _auth(token_admin)
    clinica = _crear_clinica(client_sin_auth, h_admin)
    r_vet = _crear_veterinario(client_sin_auth, h_admin, clinica["id"], matricula="MAT-V1", nombre="Dra. Ana")
    assert r_vet.status_code == 201, r_vet.text
    vet = r_vet.json()
    _crear_usuario(db, "vet1", "vetpass1", RolUsuario.VETERINARIO, veterinario_id=vet["id"])
    token_vet = _login(client_sin_auth, "vet1", "vetpass1").json()["token"]
    return {
        "h_admin": h_admin,
        "h_vet": _auth(token_vet),
        "clinica": clinica,
        "vet": vet,
        "token_vet": token_vet,
    }


# --- Modelo / validaciones ---

def test_usuario_veterinario_sin_veterinario_id_da_422(db, client_sin_auth):
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    token = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    r = client_sin_auth.post(
        "/api/usuarios",
        json={"nombre_usuario": "vetx", "contrasena": "pass1234", "rol": "VETERINARIO"},
        headers=_auth(token),
    )
    assert r.status_code == 422
    assert "veterinario_id" in r.json()["detalle"]


def test_usuario_veterinario_con_veterinario_inexistente_da_404(db, client_sin_auth):
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    token = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    r = client_sin_auth.post(
        "/api/usuarios",
        json={"nombre_usuario": "vetx", "contrasena": "pass1234", "rol": "VETERINARIO", "veterinario_id": 9999},
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_usuario_veterinario_con_veterinario_ya_vinculado_da_409(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r = client_sin_auth.post(
        "/api/usuarios",
        json={"nombre_usuario": "vet2", "contrasena": "pass1234", "rol": "VETERINARIO", "veterinario_id": ctx["vet"]["id"]},
        headers=ctx["h_admin"],
    )
    assert r.status_code == 409


def test_usuario_admin_con_veterinario_id_da_422(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r = client_sin_auth.post(
        "/api/usuarios",
        json={"nombre_usuario": "admin2", "contrasena": "pass1234", "rol": "ADMIN", "veterinario_id": ctx["vet"]["id"]},
        headers=ctx["h_admin"],
    )
    assert r.status_code == 422


# --- Alta veterinario con acceso ---

def test_alta_veterinario_con_acceso_crea_ambos(db, client_sin_auth):
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    token = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    h = _auth(token)
    clinica = _crear_clinica(client_sin_auth, h)
    r = _crear_veterinario(client_sin_auth, h, clinica["id"], matricula="MAT-A", nombre="Dra. Ana",
                           acceso={"nombre_usuario": "ana1", "contrasena": "pass1234"})
    assert r.status_code == 201
    vet = r.json()
    # el usuario debe poder loguearse
    r_login = _login(client_sin_auth, "ana1", "pass1234")
    assert r_login.status_code == 200
    assert r_login.json()["rol"] == "VETERINARIO"
    # /auth/yo debe devolver veterinario_id y nombre
    token_vet = r_login.json()["token"]
    r_yo = client_sin_auth.get("/api/auth/yo", headers=_auth(token_vet))
    assert r_yo.status_code == 200
    yo = r_yo.json()
    assert yo["veterinario_id"] == vet["id"]
    assert yo["veterinario_nombre"] == "Dra. Ana"
    assert yo["clinica_id"] == clinica["id"]
    assert yo["clinica_nombre"] == clinica["nombre"]


def test_alta_veterinario_sin_acceso_crea_solo_veterinario(db, client_sin_auth):
    _crear_usuario(db, "admin1", "adminpass", RolUsuario.ADMIN)
    token = _login(client_sin_auth, "admin1", "adminpass").json()["token"]
    h = _auth(token)
    clinica = _crear_clinica(client_sin_auth, h)
    r = _crear_veterinario(client_sin_auth, h, clinica["id"], matricula="MAT-B", nombre="Dr. B")
    assert r.status_code == 201
    # no debe existir usuario para ese vet
    from app.models.usuario import Usuario
    usuario = db.scalar(__import__("sqlalchemy").select(Usuario).where(Usuario.veterinario_id == r.json()["id"]))
    assert usuario is None


def test_si_falla_creacion_usuario_no_queda_veterinario(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    # intentar crear vet con acceso cuyo nombre_usuario ya existe (vet1)
    r = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"],
                           matricula="MAT-DUP", nombre="Dr. Dup",
                           acceso={"nombre_usuario": "vet1", "contrasena": "pass1234"})
    assert r.status_code == 409
    # el veterinario no debe existir
    r_list = client_sin_auth.get(f"/api/clinicas/{ctx['clinica']['id']}/veterinarios", headers=ctx["h_admin"])
    matriculas = [v["matricula"] for v in r_list.json()]
    assert "MAT-DUP" not in matriculas


# --- Baja de veterinario desactiva usuario ---

def test_baja_veterinario_desactiva_usuario_y_login_falla(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r_del = client_sin_auth.delete(f"/api/veterinarios/{ctx['vet']['id']}", headers=ctx["h_admin"])
    assert r_del.status_code == 204
    r_login = _login(client_sin_auth, "vet1", "vetpass1")
    assert r_login.status_code == 401


# --- Permisos "propio" en consultas y turnos ---

def _asegurar_especie(db):
    from app.models.especie import Especie
    if db.get(Especie, 1) is None:
        db.add(Especie(id=1, nombre="PERRO"))
        db.commit()


def _crear_mascota_y_cliente(db, client_sin_auth, h_admin):
    _asegurar_especie(db)
    r_cli = client_sin_auth.post("/api/clientes", json={"nombre": "Cliente T", "telefono": "123"}, headers=h_admin)
    assert r_cli.status_code == 201, r_cli.text
    cli_id = r_cli.json()["id"]
    r_masc = client_sin_auth.post("/api/mascotas", json={"nombre": "Michi", "especie_id": 1, "cliente_id": cli_id, "fecha_nacimiento": "2020-01-01"}, headers=h_admin)
    assert r_masc.status_code == 201, r_masc.text
    return r_masc.json()["id"]


def test_veterinario_no_puede_crear_consulta_de_otro_veterinario(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    # crear otro veterinario
    r_vet2 = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"], matricula="MAT-V2", nombre="Dr. Otro")
    assert r_vet2.status_code == 201
    vet2 = r_vet2.json()
    mascota_id = _crear_mascota_y_cliente(db, client_sin_auth, ctx["h_admin"])
    r = client_sin_auth.post("/api/consultas", json={
        "veterinario_id": vet2["id"], "mascota_id": mascota_id, "fecha": "2024-01-10",
        "complejidad": "BAJA", "costo": "100.00",
    }, headers=ctx["h_vet"])
    assert r.status_code == 403


def test_veterinario_puede_crear_consulta_propia(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    mascota_id = _crear_mascota_y_cliente(db, client_sin_auth, ctx["h_admin"])
    r = client_sin_auth.post("/api/consultas", json={
        "veterinario_id": ctx["vet"]["id"], "mascota_id": mascota_id, "fecha": "2024-01-10",
        "complejidad": "BAJA", "costo": "100.00",
    }, headers=ctx["h_vet"])
    assert r.status_code == 201


def test_veterinario_no_puede_crear_turno_de_otro_veterinario(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r_vet2 = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"], matricula="MAT-V3", nombre="Dr. Otro2")
    vet2 = r_vet2.json()
    mascota_id = _crear_mascota_y_cliente(db, client_sin_auth, ctx["h_admin"])
    r = client_sin_auth.post(f"/api/veterinarios/{vet2['id']}/turnos", json={
        "mascota_id": mascota_id, "inicio": "2099-01-10T09:00:00", "fin": "2099-01-10T09:30:00",
    }, headers=ctx["h_vet"])
    assert r.status_code == 403


def test_veterinario_puede_crear_turno_propio(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    mascota_id = _crear_mascota_y_cliente(db, client_sin_auth, ctx["h_admin"])
    r = client_sin_auth.post(f"/api/veterinarios/{ctx['vet']['id']}/turnos", json={
        "mascota_id": mascota_id, "inicio": "2099-01-10T09:00:00", "fin": "2099-01-10T09:30:00",
    }, headers=ctx["h_vet"])
    assert r.status_code == 201


def test_veterinario_no_puede_cancelar_turno_de_otro_veterinario(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r_vet2 = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"], matricula="MAT-V4", nombre="Dr. Otro3")
    vet2 = r_vet2.json()
    mascota_id = _crear_mascota_y_cliente(db, client_sin_auth, ctx["h_admin"])
    r_turno = client_sin_auth.post(f"/api/veterinarios/{vet2['id']}/turnos", json={
        "mascota_id": mascota_id, "inicio": "2099-01-11T09:00:00", "fin": "2099-01-11T09:30:00",
    }, headers=ctx["h_admin"])
    assert r_turno.status_code == 201
    turno_id = r_turno.json()["id"]
    r = client_sin_auth.delete(f"/api/turnos/{turno_id}", headers=ctx["h_vet"])
    assert r.status_code == 403


# --- Permisos ADMIN-only en reportes y tipos de muestra ---

def test_veterinario_no_puede_generar_reporte_y_admin_si(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r_vet = client_sin_auth.get("/api/reportes/facturacion?desde=2024-01-01&hasta=2024-12-31", headers=ctx["h_vet"])
    assert r_vet.status_code == 403
    r_admin = client_sin_auth.get("/api/reportes/facturacion?desde=2024-01-01&hasta=2024-12-31", headers=ctx["h_admin"])
    assert r_admin.status_code == 200


def test_veterinario_no_puede_crear_tipo_muestra(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r = client_sin_auth.post("/api/tipos-muestra", json={"nombre": "Sangre X", "costo_analisis": "10.00"}, headers=ctx["h_vet"])
    assert r.status_code == 403


def test_usuario_veterinario_con_veterinario_dado_de_baja_da_404(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    # dar de baja al vet (esto desactiva su usuario también, pero el vet queda inactivo)
    # crear otro vet para darlo de baja
    r_vet2 = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"], matricula="MAT-BAJA", nombre="Dr. Baja")
    assert r_vet2.status_code == 201
    vet2_id = r_vet2.json()["id"]
    r_del = client_sin_auth.delete(f"/api/veterinarios/{vet2_id}", headers=ctx["h_admin"])
    assert r_del.status_code == 204
    r = client_sin_auth.post(
        "/api/usuarios",
        json={"nombre_usuario": "vetbaja", "contrasena": "pass1234", "rol": "VETERINARIO", "veterinario_id": vet2_id},
        headers=ctx["h_admin"],
    )
    assert r.status_code == 404


def test_veterinario_no_puede_consultar_agenda_de_otro_veterinario(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r_vet2 = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"], matricula="MAT-V5", nombre="Dr. Otro4")
    vet2 = r_vet2.json()
    r = client_sin_auth.get(f"/api/veterinarios/{vet2['id']}/agenda", headers=ctx["h_vet"])
    assert r.status_code == 403


def test_veterinario_no_puede_consultar_disponibilidad_de_otro_veterinario(db, client_sin_auth):
    ctx = _setup_admin_vet(db, client_sin_auth)
    r_vet2 = _crear_veterinario(client_sin_auth, ctx["h_admin"], ctx["clinica"]["id"], matricula="MAT-V6", nombre="Dr. Otro5")
    vet2 = r_vet2.json()
    r = client_sin_auth.get(
        f"/api/veterinarios/{vet2['id']}/turnos/disponibilidad?inicio=2099-01-10T09:00:00&fin=2099-01-10T09:30:00",
        headers=ctx["h_vet"],
    )
    assert r.status_code == 403
