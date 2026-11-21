"""Integración de los cinco endpoints de reportes con el contrato común."""
import inspect

import pytest

from app.reportes import (
    ReporteAtencionesDerivaciones,
    ReporteFacturacionDesglosada,
    ReporteMuestrasRechazadas,
    ReporteTiemposPromedio,
    ReporteVacunasPendientes,
)
from app.routers import reportes as modulo_reportes

RUTAS = (
    "/api/reportes/atenciones-derivaciones",
    "/api/reportes/muestras-rechazadas",
    "/api/reportes/vacunas-pendientes",
    "/api/reportes/facturacion",
    "/api/reportes/tiempos-promedio",
)
SUBCLASES = (
    ReporteAtencionesDerivaciones,
    ReporteMuestrasRechazadas,
    ReporteVacunasPendientes,
    ReporteFacturacionDesglosada,
    ReporteTiemposPromedio,
)


def test_openapi_publica_los_cinco_endpoints(client) -> None:
    """Los cinco GET están en el contrato HTTP de la aplicación."""
    respuesta = client.get("/openapi.json")

    assert respuesta.status_code == 200
    paths = respuesta.json()["paths"]
    for ruta in RUTAS:
        assert ruta in paths
        assert "get" in paths[ruta]


def test_el_router_ya_no_tiene_todos_pendientes() -> None:
    """No queda ningún TODO de rutas de reportes sin implementar."""
    assert "TODO GET /reportes" not in inspect.getsource(modulo_reportes)


@pytest.mark.parametrize("ruta", RUTAS)
def test_los_cinco_responden_con_el_mismo_formato_sin_datos(
    client, ruta: str
) -> None:
    """Con la base sembrada pero sin operaciones: 200, filas vacías y ceros."""
    respuesta = client.get(ruta)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"titulo", "filas", "totales"}
    assert isinstance(cuerpo["titulo"], str) and cuerpo["titulo"]
    assert cuerpo["filas"] == []
    assert isinstance(cuerpo["totales"], dict)
    assert cuerpo["totales"]
    assert all(valor in (0, 0.0, "0.00") for valor in cuerpo["totales"].values())


def test_cada_reporte_declara_nombres_de_totales_unicos() -> None:
    """El nombre de cada total es propio del reporte y no una lista posicional."""
    nombres = [clase.NOMBRES_TOTALES for clase in SUBCLASES]

    assert all(isinstance(item, tuple) and item for item in nombres)
    assert len(set(nombres)) == len(SUBCLASES)
    assert all("generar" not in clase.__dict__ for clase in SUBCLASES)
