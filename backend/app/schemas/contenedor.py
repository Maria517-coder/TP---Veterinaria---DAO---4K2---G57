"""Schemas de Pydantic del módulo Contenedores de envío."""
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

TextoResponsable = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class ContenedorCrear(BaseModel):
    """El alta no necesita datos: el número es correlativo y el precinto nace intacto."""

    model_config = ConfigDict(json_schema_extra={"example": {}})


class ContenedorFiltros(BaseModel):
    """Filtros opcionales: con/sin remito y rango de fechas de las muestras."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"con_remito": True, "desde": "2020-05-01", "hasta": "2020-05-31"},
    })

    con_remito: bool | None = None
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


class MuestraAgregar(BaseModel):
    """Datos para agregar una muestra existente al contenedor (E51)."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"muestra_id": 1, "responsable": "Recepción"},
    })

    muestra_id: int = Field(ge=1)
    responsable: TextoResponsable


class RemitoGenerar(BaseModel):
    """Datos para generar el remito de un contenedor (E53)."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"laboratorio_destino": "Laboratorio Central"},
    })

    laboratorio_destino: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]


class ContenedorRespuesta(BaseModel):
    """Datos de salida de un contenedor, con el estado de su remito."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    precinto_intacto: bool
    remito_id: int | None = None
    cantidad_muestras: int = 0
