"""Frontend base: se sirve desde FastAPI y NO inserta texto con innerHTML."""
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

ARCHIVOS = (
    "index.html",
    "css/estilos.css",
    "js/api.js",
    "js/ui.js",
    "js/estado.js",
    "js/app.js",
    "js/vistas/setup.js",
)


def test_el_frontend_esta_servido_bajo_app(client) -> None:
    respuesta = client.get("/app/")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "Preparar datos" in respuesta.text
    assert "/app/js/app.js" in respuesta.text


def test_los_assets_estan_servidos(client) -> None:
    js = client.get("/app/js/app.js")
    css = client.get("/app/css/estilos.css")

    assert js.status_code == 200
    assert "montarSetup" in js.text
    assert css.status_code == 200
    assert "--acento" in css.text


def test_los_archivos_del_frontend_existen() -> None:
    for relativo in ARCHIVOS:
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
