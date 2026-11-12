"""Cálculos monetarios del dominio con fechas de consulta inclusivas."""
from datetime import date
from decimal import Decimal

import pytest

from app.models import ClinicaVeterinaria, ConsultaMedica, MuestraBiologica, TipoMuestra


def _consulta(fecha: date, costo: str, analisis: tuple[str, ...] = ()) -> ConsultaMedica:
    """Construye datos de dominio para calcular sin consultar la base."""
    return ConsultaMedica(
        fecha=fecha, costo=costo,
        muestras=[
            MuestraBiologica(
                # La fecha de muestra no debe decidir el período de facturación.
                fecha=date(2027, 1, 1),
                tipo=TipoMuestra(costo_analisis=importe),
            )
            for importe in analisis
        ],
    )


@pytest.mark.parametrize("costo,analisis,esperado", [
    ("0.10", (), "0.10"),
    ("0.10", ("0.20",), "0.30"),
    ("0.10", ("0.20", "0.20", "0.30"), "0.80"),
    ("1.005", ("2.675",), "3.69"),
    ("9999999999.99", ("1.00",), "10000000000.99"),
])
def test_costo_total(costo: str, analisis: tuple[str, ...], esperado: str) -> None:
    """Incluye cada muestra y suma importes ya normalizados sin usar float."""
    total = _consulta(date(2026, 1, 1), costo, analisis).costo_total()
    assert isinstance(total, Decimal)
    assert str(total) == esperado


@pytest.fixture()
def clinica() -> ClinicaVeterinaria:
    """Incluye consultas en ambos límites y fuera del período."""
    return ClinicaVeterinaria(consultas=[
        _consulta(date(2025, 12, 31), "100.00", ("100.00",)),
        _consulta(date(2026, 1, 1), "0.10", ("0.20", "0.20")),
        _consulta(date(2026, 1, 15), "0.20"),
        _consulta(date(2026, 1, 31), "0.30", ("0.30",)),
        _consulta(date(2026, 2, 1), "100.00", ("100.00",)),
    ])


def test_facturacion_clinica_separa_consultas_de_analisis(
    clinica: ClinicaVeterinaria,
) -> None:
    """Incluye ambos extremos y cobra solo el costo de atención clínica."""
    total = clinica.facturacion_total_clinica(date(2026, 1, 1), date(2026, 1, 31))
    assert isinstance(total, Decimal)
    assert str(total) == "0.60"


def test_facturacion_laboratorio_usa_fecha_consulta(clinica: ClinicaVeterinaria) -> None:
    """Cobra cada muestra de las consultas incluidas, aunque tenga otra fecha."""
    total = clinica.facturacion_total_laboratorio(date(2026, 1, 1), date(2026, 1, 31))
    assert isinstance(total, Decimal)
    assert str(total) == "0.70"


@pytest.mark.parametrize("metodo", [
    "facturacion_total_clinica", "facturacion_total_laboratorio",
])
@pytest.mark.parametrize("sin_consultas", [True, False])
def test_periodo_sin_datos_devuelve_cero_decimal(
    clinica: ClinicaVeterinaria, metodo: str, sin_consultas: bool,
) -> None:
    """Una colección vacía y un período sin coincidencias producen 0.00."""
    if sin_consultas:
        clinica.consultas.clear()
    total = getattr(clinica, metodo)(date(2024, 1, 1), date(2024, 1, 31))
    assert isinstance(total, Decimal)
    assert str(total) == "0.00"


def test_facturacion_por_un_solo_dia(clinica: ClinicaVeterinaria) -> None:
    """Un período con desde igual a hasta incluye las consultas de ese día."""
    dia = date(2026, 1, 1)
    assert clinica.facturacion_total_clinica(dia, dia) == Decimal("0.10")
    assert clinica.facturacion_total_laboratorio(dia, dia) == Decimal("0.40")


def test_totales_agregados_no_tienen_limite_de_columna() -> None:
    """El rango de cada precio no restringe la suma de varias consultas."""
    dia = date(2026, 1, 1)
    clinica = ClinicaVeterinaria(consultas=[
        _consulta(dia, "9999999999.99", ("9999999999.99",)),
        _consulta(dia, "9999999999.99", ("9999999999.99",)),
    ])
    assert clinica.facturacion_total_clinica(dia, dia) == Decimal("19999999999.98")
    assert clinica.facturacion_total_laboratorio(dia, dia) == Decimal("19999999999.98")
