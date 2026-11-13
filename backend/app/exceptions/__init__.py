"""Errores del dominio."""
from app.exceptions.errores import (
    ConflictoDeRecurso,
    ErrorDeDominio,
    RecursoNoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
    TurnoSuperpuesto,
)

__all__ = [
    "ConflictoDeRecurso",
    "ErrorDeDominio",
    "RecursoNoEncontrado",
    "ReglaDeNegocioViolada",
    "TransicionInvalida",
    "TurnoSuperpuesto",
]
