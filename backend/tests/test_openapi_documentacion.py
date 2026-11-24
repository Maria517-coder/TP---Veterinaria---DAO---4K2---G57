"""Documentación OpenAPI: metadatos, tags, summaries y ejemplos de entrada."""
import pytest

from app.config.settings import settings

TAGS = {
    "Clientes", "Mascotas", "Historia clínica y vacunas",
    "Clínicas y veterinarios", "Tipos de muestra", "Turnos y agenda",
    "Consultas", "Muestras", "Contenedores", "Remitos", "Reportes",
}

# Cada ruta de los endpoints de routers queda bajo una sola tag funcional.
TAGS_POR_PATH = {
    "/api/auth/login": "Autenticación",
    "/api/auth/yo": "Autenticación",
    "/api/usuarios": "Autenticación",
    "/api/clientes": "Clientes",
    "/api/clientes/{cliente_id}": "Clientes",
    "/api/clientes/{cliente_id}/mascotas": "Mascotas",
    "/api/mascotas": "Mascotas",
    "/api/mascotas/{mascota_id}": "Mascotas",
    "/api/mascotas/{mascota_id}/carnet-vacunas": "Historia clínica y vacunas",
    "/api/mascotas/{mascota_id}/historia-clinica": "Historia clínica y vacunas",
    "/api/vacunas": "Historia clínica y vacunas",
    "/api/historias-clinicas/{historia_id}/consultas": "Historia clínica y vacunas",
    "/api/historias-clinicas/{historia_id}/vacunaciones": "Historia clínica y vacunas",
    "/api/historias-clinicas/{historia_id}/vacunas-pendientes": "Historia clínica y vacunas",
    "/api/red": "Clínicas y veterinarios",
    "/api/red/clinicas": "Clínicas y veterinarios",
    "/api/clinicas": "Clínicas y veterinarios",
    "/api/clinicas/{id}": "Clínicas y veterinarios",
    "/api/clinicas/{id}/veterinarios": "Clínicas y veterinarios",
    "/api/veterinarios/{id}": "Clínicas y veterinarios",
    "/api/tipos-muestra": "Tipos de muestra",
    "/api/tipos-muestra/{id}": "Tipos de muestra",
    "/api/veterinarios/{id}/turnos": "Turnos y agenda",
    "/api/veterinarios/{id}/agenda": "Turnos y agenda",
    "/api/veterinarios/{id}/turnos/disponibilidad": "Turnos y agenda",
    "/api/turnos/{id}": "Turnos y agenda",
    "/api/consultas": "Consultas",
    "/api/consultas/{consulta_id}": "Consultas",
    "/api/consultas/{consulta_id}/muestras": "Consultas",
    "/api/consultas/{consulta_id}/orden-derivacion": "Consultas",
    "/api/consultas/{consulta_id}/comprobante": "Consultas",
    "/api/consultas/{consulta_id}/costo-total": "Consultas",
    "/api/muestras": "Muestras",
    "/api/muestras/{id}": "Muestras",
    "/api/muestras/{id}/historial-estados": "Muestras",
    "/api/muestras/{id}/resultado": "Muestras",
    "/api/contenedores": "Contenedores",
    "/api/contenedores/{id}": "Contenedores",
    "/api/contenedores/{id}/muestras": "Contenedores",
    "/api/contenedores/{id}/romper-precinto": "Contenedores",
    "/api/contenedores/{id}/remito": "Contenedores",
    "/api/remitos": "Remitos",
    "/api/remitos/{remito_id}": "Remitos",
    "/api/remitos/{remito_id}/imprimir": "Remitos",
    "/api/remitos/{remito_id}/despachar": "Remitos",
    "/api/remitos/{remito_id}/recepcion": "Remitos",
    "/api/remitos/{remito_id}/tiempo-transito": "Remitos",
    "/api/reportes/facturacion": "Reportes",
    "/api/reportes/atenciones-derivaciones": "Reportes",
    "/api/reportes/muestras-rechazadas": "Reportes",
    "/api/reportes/vacunas-pendientes": "Reportes",
    "/api/reportes/tiempos-promedio": "Reportes",
}

SCHEMAS_DE_ENTRADA = (
    "ClienteCrear", "ClienteActualizar",
    "ClinicaVeterinariaCrear", "ClinicaVeterinariaActualizar",
    "VeterinarioCrear", "VeterinarioActualizar",
    "TipoMuestraCrear", "TipoMuestraActualizar",
    "MascotaCrear", "MascotaActualizar",
    "VacunaCrear", "VacunacionCrear",
    "ConsultaCrear", "MuestraCrear",
    "ResultadoCrear",
    "ContenedorCrear", "MuestraAgregar", "RemitoGenerar",
    "ResponsableAccion",
    "TurnoCrear",
)
# Los tipos usados con Annotated[..., Query()] se expanden en parámetros de
# consulta: FastAPI no los publica como componentes, así que no llevan example.


def _esquema(client) -> dict:
    """Lee una vez el documento OpenAPI publicado por la app."""
    respuesta = client.get("/openapi.json")
    assert respuesta.status_code == 200
    return respuesta.json()


def _operaciones_de_routers(esquema: dict) -> dict[str, dict]:
    """Devuelve las 68 operaciones de routers, sin contar /api/health."""
    return {
        f"{metodo.upper()} {path}": operacion
        for path, items in esquema["paths"].items()
        if path != "/api/health"
        for metodo, operacion in items.items()
        if metodo in {"get", "post", "put", "delete", "patch"}
    }


def test_metadatos_de_la_app(client) -> None:
    info = _esquema(client)["info"]

    assert info["title"] == settings.nombre_app
    assert len(info["description"].strip()) > 50
    assert info["version"] and info["version"] != "0.1.0"


def test_tags_funcionales_tienen_descripcion(client) -> None:
    tags = {tag["name"]: tag for tag in _esquema(client).get("tags", [])}

    assert TAGS <= set(tags)
    assert "Salud" in tags
    assert all(tags[nombre].get("description", "").strip()
               for nombre in TAGS | {"Salud"})


def test_los_68_endpoints_tienen_summary_tag_y_descripcion(client) -> None:
    operaciones = _operaciones_de_routers(_esquema(client))

    assert len(operaciones) == 69
    for clave, operacion in operaciones.items():
        metodo, path = clave.split(" ", 1)
        assert operacion.get("summary", "").strip(), clave
        descripcion = operacion.get("description", "")
        assert descripcion.strip(), clave
        assert any(pista in descripcion.lower()
                   for pista in ("404", "409", "422", "errores")), clave
        assert path in TAGS_POR_PATH, f"Ruta sin tag asignada en el test: {clave}"
        assert operacion.get("tags") == [TAGS_POR_PATH[path]], clave


def test_health_tambien_esta_documentado(client) -> None:
    health = _esquema(client)["paths"]["/api/health"]["get"]

    assert health["summary"].strip()
    assert health["tags"] == ["Salud"]


@pytest.mark.parametrize("nombre", SCHEMAS_DE_ENTRADA)
def test_schema_de_entrada_tiene_ejemplo(client, nombre: str) -> None:
    esquema = _esquema(client)["components"]["schemas"][nombre]

    assert "example" in esquema, nombre
    assert isinstance(esquema["example"], dict), nombre


@pytest.mark.parametrize("nombre,campo", [
    ("TipoMuestraCrear", "costo_analisis"),
    ("TipoMuestraActualizar", "costo_analisis"),
    ("ConsultaCrear", "costo"),
])
def test_ejemplo_de_importe_es_texto_con_dos_decimales(
    client, nombre: str, campo: str
) -> None:
    ejemplo = _esquema(client)["components"]["schemas"][nombre]["example"]

    assert isinstance(ejemplo[campo], str), (nombre, campo)
    parte_entera, parte_decimal = ejemplo[campo].split(".")
    assert parte_entera.isdigit() and len(parte_decimal) == 2
