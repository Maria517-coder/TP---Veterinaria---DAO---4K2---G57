"""Schemas de Pydantic del módulo Muestras y trazabilidad."""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

EstadoMuestra = Literal[
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
]
TextoResultado = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
ResponsableResultado = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class MuestraFiltros(BaseModel):
    """Filtros opcionales y combinables para el listado de muestras."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"estado": "Recibida", "clinica_id": 1, "fecha": "2020-05-10"},
    })

    estado: EstadoMuestra | None = None
    clinica_id: int | None = Field(default=None, ge=1)
    contenedor_id: int | None = Field(default=None, ge=1)
    fecha: date | None = None


class ResultadoCrear(BaseModel):
    """Datos necesarios para procesar una muestra Recibida (E47)."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "texto": "Hemograma sin observaciones", "responsable": "Lab. Central",
        },
    })

    texto: TextoResultado
    responsable: ResponsableResultado


class MuestraRespuesta(BaseModel):
    """Datos de salida de una muestra, con el nombre del estado actual."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    consulta_id: int
    tipo_muestra_id: int
    contenedor_id: int | None
    estado: str
    fecha: date
    resultado: str | None
    fecha_resultado: date | None

    @field_validator("estado", mode="before")
    @classmethod
    def estado_a_nombre(cls, valor: object) -> object:
        """Convierte el objeto del patrón State en el nombre guardado en la base."""
        return getattr(valor, "nombre", valor)


class CambioEstadoRespuesta(BaseModel):
    """Un registro del historial inmutable de la muestra (E46)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    muestra_id: int
    estado: str
    fecha_hora: datetime
    responsable: str

    @field_validator("estado", mode="before")
    @classmethod
    def estado_a_nombre(cls, valor: object) -> object:
        """Expone el nombre del estado, no la clase interna."""
        return getattr(valor, "nombre", valor)
