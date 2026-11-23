"""Punto de entrada: crea la app, registra routers y manejadores de errores."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.database import SessionLocal, crear_tablas
from app.config.settings import settings
from app.middlewares.cors import configurar_cors
from app.middlewares.manejadores_errores import registrar_manejadores
from app.routers import (
    auth,
    clinicas,
    clientes,
    consultas,
    contenedores,
    mascotas,
    muestras,
    remitos,
    reportes,
    turnos,
    usuarios,
)
import os

from app.seeds.datos_iniciales import cargar_datos_iniciales
from app.services.usuario_service import UsuarioService

DESCRIPCION_APP = (
    "API de la red de clínicas veterinarias: administra clientes, mascotas, "
    "historias clínicas y vacunas, y gestiona la derivación de muestras "
    "biológicas a un laboratorio externo con trazabilidad completa de cada "
    'muestra. Los importes se envían siempre como texto con dos decimales, "100.00".'
)

TAGS_OPENAPI = [
    {
        "name": "Autenticación",
        "description": "Inicio de sesión, usuario actual y administración de usuarios.",
    },
    {
        "name": "Clientes",
        "description": "Responsables de las mascotas: altas, consultas, reemplazos y bajas lógicas.",
    },
    {
        "name": "Mascotas",
        "description": "Mascotas activas y su listado por cliente; cada alta crea su historia clínica.",
    },
    {
        "name": "Historia clínica y vacunas",
        "description": "Historia clínica, vacunaciones, vacunas obligatorias pendientes y carnet en PDF.",
    },
    {
        "name": "Clínicas y veterinarios",
        "description": "Clínicas de la red y los veterinarios que atienden en cada una.",
    },
    {
        "name": "Tipos de muestra",
        "description": "Catálogo de tipos de muestra biológica y el costo de su análisis.",
    },
    {
        "name": "Turnos y agenda",
        "description": "Reserva, consulta y cancelación de turnos; la agenda se calcula con los turnos vigentes.",
    },
    {
        "name": "Consultas",
        "description": "Atenciones clínicas, muestras asociadas, orden de derivación, comprobante y costo total.",
    },
    {
        "name": "Muestras",
        "description": "Trazabilidad de muestras: estados, historial inmutable y carga de resultados.",
    },
    {
        "name": "Contenedores",
        "description": "Contenedores físicos de envío, precinto y generación del remito asociado.",
    },
    {
        "name": "Remitos",
        "description": "Trámite de envío: despacho, recepción, impresión en PDF y tiempo de tránsito.",
    },
    {
        "name": "Reportes",
        "description": "Facturación, derivaciones, rechazos, vacunas pendientes y tiempos promedio.",
    },
    {
        "name": "Salud",
        "description": "Comprobación rápida de que la API está levantada.",
    },
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    crear_tablas()
    with SessionLocal() as db:
        with db.begin():
            cargar_datos_iniciales(db)
        if os.getenv("TESTING") != "1":
            UsuarioService(db).asegurar_admin_inicial(
                os.getenv("ADMIN_PASSWORD", "admin123")
            )
    yield


app = FastAPI(
    title=settings.nombre_app,
    description=DESCRIPCION_APP,
    version="1.0.0",
    openapi_tags=TAGS_OPENAPI,
    lifespan=lifespan,
)

configurar_cors(app)
registrar_manejadores(app)

for modulo in (
    auth,
    clinicas,
    clientes,
    mascotas,
    turnos,
    consultas,
    muestras,
    contenedores,
    remitos,
    reportes,
    usuarios,
):
    app.include_router(modulo.router, prefix="/api")


@app.get(
    "/api/health",
    tags=["Salud"],
    summary="Comprobar el estado de la API",
    description='Devuelve `{"estado": "ok"}`. Sin errores de dominio.',
)
def health() -> dict[str, str]:
    return {"estado": "ok"}


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
