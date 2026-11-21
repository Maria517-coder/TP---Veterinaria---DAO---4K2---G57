"""Contrato común del Template Method y del JSON de los reportes."""
import json
from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.exceptions import ReglaDeNegocioViolada
from app.reportes import (
    FiltroReporte,
    Reporte,
    ReporteAtencionesDerivaciones,
    ReporteFacturacionDesglosada,
    ReporteMuestrasRechazadas,
    ReporteTiemposPromedio,
    ReporteVacunasPendientes,
    ResultadoReporte,
)
from app.schemas.reporte import FiltroReporteRequest, ReporteRespuesta, totales_nombrados

SUBCLASES = (
    ReporteAtencionesDerivaciones,
    ReporteMuestrasRechazadas,
    ReporteVacunasPendientes,
    ReporteFacturacionDesglosada,
    ReporteTiemposPromedio,
)


class ReporteEjemplo(Reporte):
    """Subclase concreta mínima para probar los pasos comunes sin tocar la DB."""

    NOMBRES_TOTALES = ("importe", "cantidad")

    def __init__(self) -> None:
        self.pasos: list[str] = []

    def validar_filtro(self, filtro: FiltroReporte) -> None:
        self.pasos.append("validar")
        super().validar_filtro(filtro)

    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        self.pasos.append("obtener")
        return [filtro]

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        self.pasos.append("calcular")
        return ResultadoReporte(
            titulo="Ejemplo", filas=[{"dato": 1}],
            totales=[Decimal("1.50"), 2],
        )

    def formatear(self, resultado: ResultadoReporte) -> ResultadoReporte:
        self.pasos.append("formatear")
        return super().formatear(resultado)


def test_generar_respeta_el_orden_de_los_pasos() -> None:
    """La plantilla llama a validar, obtener, calcular y formatear, en ese orden."""
    reporte = ReporteEjemplo()
    resultado = reporte.generar(FiltroReporte())

    assert reporte.pasos == ["validar", "obtener", "calcular", "formatear"]
    assert resultado.titulo == "Ejemplo"


@pytest.mark.parametrize("clase", SUBCLASES)
def test_ninguna_subclase_sobrescribe_generar(clase: type[Reporte]) -> None:
    """El patrón Template Method exige heredar generar() sin redefinirlo."""
    assert "generar" not in clase.__dict__


def test_validar_filtro_rechaza_rango_invertido() -> None:
    """Un período al revés no llega a la consulta de datos."""
    hoy = date.today()
    filtro = FiltroReporte(desde=hoy, hasta=hoy - timedelta(days=1))

    with pytest.raises(ReglaDeNegocioViolada):
        ReporteEjemplo().generar(filtro)


def test_validar_filtro_rechaza_clinica_invalida() -> None:
    """Los ids de clínica empiezan en 1, también al llamar al reporte directo."""
    with pytest.raises(ReglaDeNegocioViolada):
        ReporteEjemplo().generar(FiltroReporte(clinica_id=0))


def test_validar_filtro_acepta_filtro_valido() -> None:
    """Un rango correcto y una clínica válida dejan pasar la generación."""
    hoy = date.today()
    filtro = FiltroReporte(desde=hoy - timedelta(days=7), hasta=hoy, clinica_id=1)

    assert ReporteEjemplo().generar(filtro).titulo == "Ejemplo"


def test_formatear_devuelve_una_copia_sin_compartir_colecciones() -> None:
    """El resultado entregado no comparte filas ni totales con el calculado."""
    original = ResultadoReporte(
        titulo="Original", filas=[{"a": 1}], totales=[Decimal("3.00")],
    )

    copia = ReporteEjemplo().formatear(original)
    copia.filas.append({"a": 2})
    copia.totales.append(4)

    assert copia is not original
    assert original.filas == [{"a": 1}]
    assert original.totales == [Decimal("3.00")]


def test_totales_nombrados_empareja_nombres_y_conserva_tipos() -> None:
    """El adapter convierte la lista posicional en nombre → valor, sin convertir Decimal."""
    totales = totales_nombrados(("importe", "cantidad"), [Decimal("12.34"), 5])

    assert totales == {"importe": Decimal("12.34"), "cantidad": 5}
    assert isinstance(totales["importe"], Decimal)


def test_totales_nombrados_rechaza_cantidad_distinta() -> None:
    """Un desajuste entre nombres y valores se detecta antes de responder."""
    with pytest.raises(ValueError):
        totales_nombrados(("importe", "cantidad"), [Decimal("12.34")])


def test_schema_rechaza_rango_invertido() -> None:
    """La validación de la request responde 422 antes de llegar al service."""
    hoy = date.today()
    with pytest.raises(ValidationError):
        FiltroReporteRequest(desde=hoy, hasta=hoy - timedelta(days=1))


def test_schema_rechaza_clinica_id_no_positivo() -> None:
    """El schema no acepta ids de clínica menores a 1."""
    with pytest.raises(ValidationError):
        FiltroReporteRequest(clinica_id=0)


def test_respuesta_serializa_decimal_como_texto() -> None:
    """Los importes siguen siendo Decimal y viajan como texto en el JSON."""
    respuesta = ReporteRespuesta(
        titulo="Facturación", filas=[{"clinica": "Centro"}],
        totales={"atenciones": Decimal("12.34"), "muestras": 2},
    )

    datos = json.loads(respuesta.model_dump_json())

    assert datos["totales"] == {"atenciones": "12.34", "muestras": 2}
    assert datos["filas"] == [{"clinica": "Centro"}]


def test_respuesta_admite_reporte_sin_datos() -> None:
    """Un reporte vacío tiene un representante válido: filas vacías y ceros."""
    respuesta = ReporteRespuesta(
        titulo="Sin datos", filas=[],
        totales={"atenciones": Decimal("0.00"), "muestras": 0},
    )

    assert respuesta.filas == []
    assert respuesta.totales["atenciones"] == Decimal("0.00")


def test_schema_no_depende_de_una_sesion() -> None:
    """Los schemas son solo contrato: no reciben la sesión de base de datos."""
    assert set(FiltroReporteRequest.model_fields) == {"desde", "hasta", "clinica_id"}
    assert set(ReporteRespuesta.model_fields) == {"titulo", "filas", "totales"}
