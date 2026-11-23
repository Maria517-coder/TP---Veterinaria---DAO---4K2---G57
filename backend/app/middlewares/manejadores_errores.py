"""Traduce las excepciones del dominio a respuestas HTTP (404, 409 y 422)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    AccesoProhibido,
    ConflictoDeRecurso,
    ErrorDeDominio,
    NoAutenticado,
    RecursoNoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
    TurnoSuperpuesto,
)

_CODIGOS: dict[type[ErrorDeDominio], int] = {
    RecursoNoEncontrado: 404,
    TransicionInvalida: 409,
    TurnoSuperpuesto: 409,
    ConflictoDeRecurso: 409,
    ReglaDeNegocioViolada: 422,
    NoAutenticado: 401,
    AccesoProhibido: 403,
}


def registrar_manejadores(app: FastAPI) -> None:
    async def manejar_error_de_dominio(_solicitud: Request, error: ErrorDeDominio) -> JSONResponse:
        codigo = _CODIGOS.get(type(error), 400)
        return JSONResponse(status_code=codigo, content={"detalle": error.mensaje})

    app.add_exception_handler(ErrorDeDominio, manejar_error_de_dominio)
