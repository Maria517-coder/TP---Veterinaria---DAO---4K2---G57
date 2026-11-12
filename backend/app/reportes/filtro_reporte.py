"""Parámetros comunes de todos los reportes."""
from dataclasses import dataclass
from datetime import date


@dataclass
class FiltroReporte:
    desde: date | None = None
    hasta: date | None = None
    clinica_id: int | None = None
