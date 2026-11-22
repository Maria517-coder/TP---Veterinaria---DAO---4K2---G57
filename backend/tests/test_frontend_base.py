"""Frontend base: esqueleto servido, sin innerHTML y con JS parseable."""
import shutil
import subprocess
from pathlib import Path

import pytest

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

ARCHIVOS_R1 = (
    "index.html",
    "css/estilos.css",
    "js/api.js",
    "js/ui.js",
    "js/estado.js",
    "js/app.js",
    "js/router.js",
    "js/vistas/inicio.js",
)

HASHES_MENU = (
    "#/inicio",
    "#/clinicas",
    "#/recepcion",
    "#/consultorio",
    "#/turnos",
    "#/laboratorio",
    "#/reportes",
)


def test_el_frontend_esta_servido_bajo_app(client) -> None:
    respuesta = client.get("/app/")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    cuerpo = respuesta.text
    assert 'id="app"' in cuerpo
    assert 'id="sidebar"' in cuerpo
    for hash_ruta in HASHES_MENU:
        assert hash_ruta in cuerpo, hash_ruta
    assert "/app/js/app.js" in cuerpo


def test_los_assets_estan_servidos(client) -> None:
    for ruta, esperado in (
        ("/app/js/app.js", "iniciar"),
        ("/app/js/router.js", "registrarRuta"),
        ("/app/js/vistas/inicio.js", "Inicio"),
        ("/app/css/estilos.css", "--acento"),
    ):
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert esperado in respuesta.text, ruta


def test_los_archivos_del_esqueleto_existen() -> None:
    for relativo in ARCHIVOS_R1:
        assert (FRONTEND / relativo).is_file(), relativo


def test_el_frontend_no_usa_innerhtml() -> None:
    for archivo in FRONTEND.rglob("*.js"):
        contenido = archivo.read_text(encoding="utf-8")
        assert "innerHTML" not in contenido, str(archivo)


def test_api_y_ui_tienen_el_contrato_de_errores_y_texto() -> None:
    api = (FRONTEND / "js/api.js").read_text(encoding="utf-8")
    ui = (FRONTEND / "js/ui.js").read_text(encoding="utf-8")

    assert '"detalle"' in api
    assert '"detail"' in api
    assert "textContent" in ui


def test_js_tiene_sintaxis_valida_con_node() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node no está instalado; se omite node --check")

    for archivo in sorted(FRONTEND.rglob("*.js")):
        resultado = subprocess.run(
            [node, "--check", str(archivo)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert resultado.returncode == 0, (
            f"{archivo.relative_to(FRONTEND)}:\n"
            f"{resultado.stderr or resultado.stdout}"
        )
