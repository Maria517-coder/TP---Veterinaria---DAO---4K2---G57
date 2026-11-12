"""Errores del dominio."""
from app.exceptions.errores import (
    ErrorDeDominio,
    RecursoNoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
    TurnoSuperpuesto,
)

__all__ = [
    "ErrorDeDominio",
    "RecursoNoEncontrado",
    "ReglaDeNegocioViolada",
    "TransicionInvalida",
    "TurnoSuperpuesto",
]
