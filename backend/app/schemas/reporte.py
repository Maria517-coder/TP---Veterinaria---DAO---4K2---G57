"""Schemas de Pydantic del módulo Reportes (filtros y resultados)."""
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FiltroReporteRequest(BaseModel):
    """Filtros opcionales compartidos por los cinco reportes."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "desde": "2020-05-01", "hasta": "2020-05-31", "clinica_id": 1,
        },
    })

    desde: date | None = None
    hasta: date | None = None
    clinica_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def rango_valido(self) -> "FiltroReporteRequest":
        """Rechaza los rangos invertidos antes de llegar al service."""
        if (
            self.desde is not None
            and self.hasta is not None
            and self.desde > self.hasta
        ):
            raise ValueError("'desde' no puede ser posterior a 'hasta'")
        return self


class ReporteRespuesta(BaseModel):
    """Respuesta JSON común: filas como objetos y totales por nombre."""

    model_config = ConfigDict(from_attributes=True)

    titulo: str
    filas: list[dict[str, Any]]
    totales: dict[str, Decimal | int | float]


def totales_nombrados(
    nombres: Sequence[str], totales: Sequence[Decimal | int | float]
) -> dict[str, Decimal | int | float]:
    """Convierte los totales posicionales del contrato en un objeto por nombre.

    ``ResultadoReporte`` conserva su contrato (lista posicional); solo el JSON
    cambia a ``nombre → valor``. Los importes siguen siendo ``Decimal``.
    """
    if len(nombres) != len(totales):
        raise ValueError(
            f"Hay {len(nombres)} nombres y {len(totales)} totales; deben coincidir"
        )
    return dict(zip(nombres, totales))
