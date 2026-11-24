"""Configuración de pytest: usa una base SQLite aparte para los tests."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_veterinaria.sqlite"
os.environ["TESTING"] = "1"

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config.database import Base, SessionLocal, crear_tablas, engine  # noqa: E402
from app.core.dependencias import obtener_usuario_actual, requiere_admin  # noqa: E402
from app.main import app  # noqa: E402
from app.models.usuario import RolUsuario, Usuario  # noqa: E402


@pytest.fixture(autouse=True)
def _autenticar_como_admin() -> Generator[None, None, None]:
    """Los tests existentes corren como ADMIN; los de seguridad quitan este override."""
    admin = Usuario(
        id=1,
        nombre_usuario="test_admin",
        contrasena_hash="no-expuesto",
        rol=RolUsuario.ADMIN.value,
        activo=True,
    )
    app.dependency_overrides[obtener_usuario_actual] = lambda: admin
    app.dependency_overrides[requiere_admin] = lambda: admin
    yield
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    app.dependency_overrides.pop(requiere_admin, None)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Entrega una sesin sobre una base de test vaca y la deja limpia al terminar."""
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
