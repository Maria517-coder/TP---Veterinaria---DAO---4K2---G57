"""Schemas de Pydantic del módulo Agenda y turnos."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TurnoCrear(BaseModel):
    """Datos de entrada para reservar un turno."""

    mascota_id: int
    inicio: datetime
    fin: datetime

    @field_validator("mascota_id")
    @classmethod
    def id_positivo(cls, valor: int) -> int:
        if valor < 1:
            raise ValueError("El id de la mascota debe ser positivo")
        return valor

    @field_validator("inicio")
    @classmethod
    def no_puede_ser_pasado(cls, valor: datetime) -> datetime:
        """La regla depende solo del dato: se resuelve en el schema."""
        if valor < datetime.now():
            raise ValueError("El inicio del turno no puede ser pasado")
        return valor

    @field_validator("fin")
    @classmethod
    def posterior_al_inicio(cls, valor: datetime, info) -> datetime:
        inicio = info.data.get("inicio")
        if inicio is not None and valor <= inicio:
            raise ValueError("El fin del turno debe ser posterior al inicio")
        return valor


class TurnoDisponibilidad(BaseModel):
    """Intervalo a consultar antes de reservar."""

    inicio: datetime
    fin: datetime

    @field_validator("inicio")
    @classmethod
    def no_puede_ser_pasado(cls, valor: datetime) -> datetime:
        if valor < datetime.now():
            raise ValueError("El inicio no puede ser pasado")
        return valor

    @field_validator("fin")
    @classmethod
    def posterior_al_inicio(cls, valor: datetime, info) -> datetime:
        inicio = info.data.get("inicio")
        if inicio is not None and valor <= inicio:
            raise ValueError("El fin debe ser posterior al inicio")
        return valor


class TurnoRespuesta(BaseModel):
    """Datos de salida de un turno."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    veterinario_id: int
    mascota_id: int
    inicio: datetime
    fin: datetime
    activo: bool
