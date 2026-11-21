"""Validación de los schemas de tipos de muestra."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.tipo_muestra import TipoMuestraActualizar, TipoMuestraCrear


@pytest.mark.parametrize("nombre", ["", "   ", "\t\n", "N" * 101])
def test_nombre_invalido(nombre: str) -> None:
    """El nombre no puede ser vacío ni superar los 100 caracteres."""
    with pytest.raises(ValidationError):
        TipoMuestraCrear(nombre=nombre, costo_analisis=Decimal("1500.00"))


def test_nombre_se_recorta() -> None:
    """Los espacios de los extremos se descartan."""
    tipo = TipoMuestraCrear(nombre="  SANGRE  ", costo_analisis=Decimal("1500.00"))

    assert tipo.nombre == "SANGRE"


def test_costo_acepta_decimal_y_cadena() -> None:
    """Decimal y cadena llegan al modelo como Decimal."""
    desde_decimal = TipoMuestraCrear(
        nombre="SANGRE", costo_analisis=Decimal("1500.00")
    )
    desde_cadena = TipoMuestraCrear(nombre="ORINA", costo_analisis="1200.05")

    assert desde_decimal.costo_analisis == Decimal("1500.00")
    assert desde_cadena.costo_analisis == Decimal("1200.05")


def test_costo_rechaza_float() -> None:
    """Un float nunca llega a normalizar_importe: se rechaza en el schema."""
    with pytest.raises(ValidationError):
        TipoMuestraCrear(nombre="SANGRE", costo_analisis=1500.5)


def test_costo_rechaza_importe_negativo() -> None:
    """El costo de análisis no puede ser negativo."""
    with pytest.raises(ValidationError):
        TipoMuestraCrear(nombre="SANGRE", costo_analisis=Decimal("-0.01"))


def test_costo_cero_es_valido() -> None:
    """Cero está permitido (solo se rechaza menor que cero)."""
    tipo = TipoMuestraCrear(nombre="GRATIS", costo_analisis=0)

    assert tipo.costo_analisis == Decimal("0")


def test_actualizar_valida_igual_que_crear() -> None:
    """El PUT comparte las validaciones del alta."""
    with pytest.raises(ValidationError):
        TipoMuestraActualizar(nombre="SANGRE", costo_analisis=1500.5)
    with pytest.raises(ValidationError):
        TipoMuestraActualizar(nombre="SANGRE", costo_analisis=Decimal("-1"))


def test_decimal_se_serializa_como_texto() -> None:
    """JSON representa el importe como cadena, sin convertirlo en float."""
    tipo = TipoMuestraCrear(nombre="SANGRE", costo_analisis=Decimal("1500.00"))

    assert tipo.model_dump()["costo_analisis"] == Decimal("1500.00")
    assert tipo.model_dump(mode="json")["costo_analisis"] == "1500.00"
