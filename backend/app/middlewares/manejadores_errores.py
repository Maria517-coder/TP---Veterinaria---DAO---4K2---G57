"""Traduce las excepciones del dominio a respuestas HTTP (404, 409 y 422)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    ErrorDeDominio,
    RecursoNoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
    TurnoSuperpuesto,
)

_CODIGOS: dict[type[ErrorDeDominio], int] = {
    RecursoNoEncontrado: 404,
    TransicionInvalida: 409,
    TurnoSuperpuesto: 409,
    ReglaDeNegocioViolada: 422,
}


def registrar_manejadores(app: FastAPI) -> None:
    async def manejar_error_de_dominio(_solicitud: Request, error: ErrorDeDominio) -> JSONResponse:
        codigo = _CODIGOS.get(type(error), 400)
        return JSONResponse(status_code=codigo, content={"detalle": error.mensaje})

    app.add_exception_handler(ErrorDeDominio, manejar_error_de_dominio)
