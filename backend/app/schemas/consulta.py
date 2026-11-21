"""Schemas de Pydantic del módulo Consultas y derivación."""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.models.complejidad import Complejidad


def _validar_costo(valor: object) -> Decimal:
    """Rechaza float y negativos antes de que Pydantic convierta el valor a Decimal."""
    if isinstance(valor, bool) or isinstance(valor, float):
        raise ValueError("El costo debe ser Decimal, cadena o entero; no float")
    if not isinstance(valor, (Decimal, str, int)):
        raise ValueError("El costo debe ser Decimal, cadena o entero")
    try:
        importe = Decimal(valor)
    except InvalidOperation as error:
        raise ValueError("El costo no es un número decimal válido") from error
    if not importe.is_finite() or importe < 0:
        raise ValueError("El costo debe ser finito y no negativo")
    return importe


Costo = Annotated[Decimal, BeforeValidator(_validar_costo)]


class ConsultaCrear(BaseModel):
    """Datos de entrada para registrar una atención."""

    veterinario_id: int
    mascota_id: int
    fecha: date
    complejidad: Complejidad
    costo: Costo

    @field_validator("fecha")
    @classmethod
    def no_puede_ser_futura(cls, valor: date) -> date:
        """Una consulta no puede registrarse con fecha futura."""
        if valor > date.today():
            raise ValueError("La fecha de la consulta no puede ser futura")
        return valor


class MuestraCrear(BaseModel):
    """Datos de entrada para crear una muestra: solo se elige su tipo."""

    tipo_muestra_id: int

    @field_validator("tipo_muestra_id")
    @classmethod
    def debe_ser_positivo(cls, valor: int) -> int:
        if valor < 1:
            raise ValueError("El tipo de muestra debe ser un id positivo")
        return valor


class VacunaPendienteRespuesta(BaseModel):
    """Vacuna obligatoria aún no aplicada, avisada al registrar la consulta."""

    id: int
    nombre: str


class ConsultaRespuesta(BaseModel):
    """Datos de salida de una consulta, con el aviso de vacunas pendientes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    clinica_id: int
    veterinario_id: int
    mascota_id: int
    fecha: date
    complejidad: Complejidad
    costo: Decimal
    vacunas_pendientes: list[VacunaPendienteRespuesta] = Field(default_factory=list)


class MuestraRespuesta(BaseModel):
    """Datos de salida de una muestra biológica."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    consulta_id: int
    tipo_muestra_id: int
    estado: str
    fecha: date
    resultado: str | None = None

    @field_validator("estado", mode="before")
    @classmethod
    def nombre_del_estado(cls, valor: object) -> str:
        """La propiedad `estado` da un objeto del patrón State; mostramos su nombre."""
        return str(getattr(valor, "nombre", valor))


class CostoTotalRespuesta(BaseModel):
    """Total facturable de una consulta, como Decimal (texto en JSON)."""

    costo_total: Decimal
