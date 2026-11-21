"""Schemas de Pydantic del módulo Remitos biológicos."""
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.models.estado_remito import EstadoRemito

Responsable = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class RemitoFiltros(BaseModel):
    """Filtros opcionales: estado, clínica de origen y rango de fechas de emisión."""

    estado: EstadoRemito | None = None
    clinica_id: int | None = None
    desde: date | None = None
    hasta: date | None = None

    @field_validator("hasta")
    @classmethod
    def rango_valido(cls, valor: date | None, info) -> date | None:
        """Un rango invertido no tiene sentido y se rechaza en el schema (422)."""
        desde = info.data.get("desde")
        if desde is not None and valor is not None and valor < desde:
            raise ValueError("La fecha hasta no puede ser anterior a la fecha desde")
        return valor


class ResponsableAccion(BaseModel):
    """Responsable de una acción de despacho o recepción (E58/E59)."""

    responsable: Responsable


class RemitoRespuesta(BaseModel):
    """Datos de salida de un remito, con su estado actual."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    fecha_emision: datetime
    clinica_origen_id: int
    laboratorio_destino: str
    estado: EstadoRemito
    fecha_hora_despacho: datetime | None = None
    fecha_hora_recepcion: datetime | None = None
    contenedor_id: int


class TiempoTransitoRespuesta(BaseModel):
    """Diferencia entre la recepción y el despacho, en segundos (E60)."""

    tiempo_transito: float
