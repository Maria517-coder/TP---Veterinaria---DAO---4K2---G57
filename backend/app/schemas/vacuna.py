"""Contratos del catálogo de vacunas."""
from datetime import date
from pydantic import BaseModel, ConfigDict

from app.schemas.mascota import Nombre


class VacunaCrear(BaseModel):
    """Datos de alta con los identificadores de especies aplicables."""

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

    vacuna_id: int
    fecha: date


class VacunacionRespuesta(BaseModel):
    """Datos de una aplicación guardada en la historia."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    historia_clinica_id: int
    vacuna_id: int
    fecha: date
