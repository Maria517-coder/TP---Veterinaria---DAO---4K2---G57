"""Errores del dominio."""
from app.exceptions.errores import (
    AccesoProhibido,
    ConflictoDeRecurso,
    ErrorDeDominio,
    NoAutenticado,
    RecursoNoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
    TurnoSuperpuesto,
)

__all__ = [
    "AccesoProhibido",
    "ConflictoDeRecurso",
    "ErrorDeDominio",
    "NoAutenticado",
    "RecursoNoEncontrado",
    "ReglaDeNegocioViolada",
    "TransicionInvalida",
    "TurnoSuperpuesto",
]
