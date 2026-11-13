"""Punto de entrada: crea la app, registra routers y manejadores de errores."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.database import SessionLocal, crear_tablas
from app.config.settings import settings
from app.middlewares.cors import configurar_cors
from app.middlewares.manejadores_errores import registrar_manejadores
from app.routers import (
    clientes,
    consultas,
    contenedores,
    mascotas,
    muestras,
    remitos,
    reportes,
    turnos,
)
from app.seeds.datos_iniciales import cargar_datos_iniciales


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    crear_tablas()
    with SessionLocal() as db:
        with db.begin():
            cargar_datos_iniciales(db)
    yield


app = FastAPI(title=settings.nombre_app, lifespan=lifespan)

configurar_cors(app)
registrar_manejadores(app)

# Volver a registrar clínicas cuando estén disponibles sus schemas y servicios.
for modulo in (
    clientes,
    mascotas,
    turnos,
    consultas,
    muestras,
    contenedores,
    remitos,
    reportes,
):
    app.include_router(modulo.router, prefix="/api")


@app.get("/api/health", tags=["Salud"])
def health() -> dict[str, str]:
    return {"estado": "ok"}
