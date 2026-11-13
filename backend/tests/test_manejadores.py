"""El manejador global traduce las excepciones de dominio a HTTP."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import ConflictoDeRecurso
from app.middlewares.manejadores_errores import registrar_manejadores


def test_conflicto_de_recurso_devuelve_409() -> None:
    """Una excepción ConflictoDeRecurso se traduce a 409 con el formato del dominio."""
    app = FastAPI()
    registrar_manejadores(app)

    @app.get("/conflicto")
    def conflicto() -> None:
        raise ConflictoDeRecurso("El cliente tiene mascotas")

    with TestClient(app, raise_server_exceptions=False) as cliente:
        respuesta = cliente.get("/conflicto")

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detalle": "El cliente tiene mascotas"}
