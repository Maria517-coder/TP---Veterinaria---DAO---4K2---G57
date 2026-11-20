"""Schemas de Pydantic del módulo Tipos de muestra."""
from decimal import Decimal, InvalidOperation
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints

Nombre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


def _validar_costo_analisis(valor: object) -> Decimal:
    """Rechaza float y negativos antes de que Pydantic convierta el valor a Decimal."""
    if isinstance(valor, bool) or isinstance(valor, float):
        raise ValueError("El costo de análisis debe ser Decimal, cadena o entero; no float")
    if not isinstance(valor, (Decimal, str, int)):
        raise ValueError("El costo de análisis debe ser Decimal, cadena o entero")
    try:
        importe = Decimal(valor)
    except InvalidOperation as error:
        raise ValueError("El costo de análisis no es un número decimal válido") from error
    if not importe.is_finite() or importe < 0:
        raise ValueError("El costo de análisis debe ser finito y no negativo")
    return importe


CostoAnalisis = Annotated[Decimal, BeforeValidator(_validar_costo_analisis)]


class TipoMuestraCrear(BaseModel):
    """Datos de entrada para dar de alta un tipo de muestra."""

    nombre: Nombre
    costo_analisis: CostoAnalisis


class TipoMuestraActualizar(BaseModel):
    """Datos de entrada para reemplazar un tipo de muestra (PUT)."""

    nombre: Nombre
    costo_analisis: CostoAnalisis


class TipoMuestraRespuesta(BaseModel):
    """Datos de salida de un tipo de muestra."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    costo_analisis: Decimal
