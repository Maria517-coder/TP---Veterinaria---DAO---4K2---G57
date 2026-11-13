"""Schemas de Pydantic del módulo Mascotas."""
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

Nombre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class MascotaBase(BaseModel):
    """Campos y validaciones compartidas por el alta y el reemplazo."""

    cliente_id: int
    especie_id: int
    nombre: Nombre
    fecha_nacimiento: date

    @field_validator("fecha_nacimiento")
    @classmethod
    def no_puede_ser_futura(cls, valor: date) -> date:
        """Una mascota no puede haber nacido después de hoy."""
        if valor > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        return valor


class MascotaCrear(MascotaBase):
    """Datos de entrada para dar de alta una mascota."""


class MascotaActualizar(MascotaBase):
    """Datos de entrada para reemplazar una mascota (PUT)."""


class MascotaRespuesta(BaseModel):
    """Datos de salida de una mascota."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    especie_id: int
    nombre: str
    fecha_nacimiento: date
    activo: bool


class HistoriaClinicaRespuesta(BaseModel):
    """Identificación de la historia clínica asociada a una mascota."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mascota_id: int
    numero: int
