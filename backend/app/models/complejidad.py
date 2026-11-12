"""Complejidad de una consulta médica."""
import enum


class Complejidad(str, enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
