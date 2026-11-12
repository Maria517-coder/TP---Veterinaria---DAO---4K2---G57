"""Verifica que todas las clases del dominio se mapean y sus relaciones se resuelven."""
from sqlalchemy.orm import configure_mappers

import app.models  # noqa: F401  (registra todos los modelos)


def test_mapeo_de_modelos_correcto() -> None:
    configure_mappers()
