"""Configuración de pytest: usa una base SQLite aparte para los tests."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_veterinaria.sqlite"

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config.database import Base, SessionLocal, crear_tablas, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Entrega una sesión sobre una base de test vacía y la deja limpia al terminar."""
    crear_tablas()  # importa app.models y registra todas las tablas en Base.metadata
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.rollback()
        sesion.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP contra la app real, con la base de test limpia por test."""
    with TestClient(app) as cliente:
        yield cliente
