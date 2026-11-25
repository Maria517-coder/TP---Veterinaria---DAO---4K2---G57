"""Contratos del catálogo de vacunas."""
from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.mascota import Nombre


class VacunaCrear(BaseModel):
    """Datos de alta con los identificadores de especies aplicables."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "nombre": "Rabia", "obligatoria": True, "especies_aplicables": [1],
        },
    })

    nombre: Nombre
    obligatoria: bool = False
    especies_aplicables: list[int]


class EspecieRespuesta(BaseModel):
    """Identificación de una especie del catálogo."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class VacunaRespuesta(BaseModel):
    """Vacuna y especies para las que está catalogada."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    obligatoria: bool
    especies_aplicables: list[EspecieRespuesta]


class VacunacionCrear(BaseModel):
    """Vacuna aplicada y fecha registrada."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"vacuna_id": 1, "fecha": "2020-05-10"},
    })

    vacuna_id: int
    fecha: date

    @field_validator("fecha")
    @classmethod
    def no_puede_ser_futura(cls, valor: date) -> date:
        """Una vacuna solo se registra como aplicada si la fecha no es posterior a hoy."""
        if valor > date.today():
            raise ValueError("La fecha de vacunación no puede ser futura")
        return valor


class VacunacionRespuesta(BaseModel):
    """Datos de una aplicación guardada en la historia."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    historia_clinica_id: int
    vacuna_id: int
    fecha: date
