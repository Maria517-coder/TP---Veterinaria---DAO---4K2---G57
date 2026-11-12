"""Resultado que devuelven todos los reportes."""
from dataclasses import dataclass, field


@dataclass
class ResultadoReporte:
    titulo: str
    filas: list[object] = field(default_factory=list)
    totales: list[float] = field(default_factory=list)
