"""Resultado que devuelven todos los reportes."""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ResultadoReporte:
    """Conserva dinero como Decimal, cantidades como int y tiempos como float."""

    titulo: str
    filas: list[object] = field(default_factory=list)
    totales: list[Decimal | int | float] = field(default_factory=list)
