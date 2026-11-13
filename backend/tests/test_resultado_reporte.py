"""Contrato numérico común para futuros reportes de dinero, cantidades y tiempos."""
from decimal import Decimal
from typing import get_args, get_type_hints

from app.reportes.resultado_reporte import ResultadoReporte


def test_contrato_admite_importes_decimales() -> None:
    """El contrato público debe permitir dinero Decimal sin convertirlo a float."""
    tipo_elemento = get_args(get_type_hints(ResultadoReporte)["totales"])[0]
    tipos_permitidos = get_args(tipo_elemento)
    assert Decimal in tipos_permitidos
    assert float in tipos_permitidos


def test_conserva_importes_cantidades_y_tiempos() -> None:
    """Los futuros reportes pueden devolver cada magnitud con su tipo adecuado."""
    resultado = ResultadoReporte(
        titulo="Prueba de contrato",
        totales=[Decimal("0.10") + Decimal("0.20"), 2, 1.5],
    )
    importe, cantidad, tiempo = resultado.totales
    assert isinstance(importe, Decimal)
    assert str(importe) == "0.30"
    assert isinstance(cantidad, int)
    assert isinstance(tiempo, float)


def test_conserva_totales_monetarios_mayores_al_limite_de_columna() -> None:
    """El resultado agregado no se restringe al rango de un precio persistido."""
    resultado = ResultadoReporte(titulo="Total", totales=[Decimal("19999999999.98")])
    assert resultado.totales == [Decimal("19999999999.98")]


def test_resultados_no_comparten_colecciones() -> None:
    """Agregar un total a un resultado no modifica otro resultado independiente."""
    primero = ResultadoReporte(titulo="Primero")
    segundo = ResultadoReporte(titulo="Segundo")
    primero.totales.append(Decimal("1.00"))
    assert segundo.totales == []
