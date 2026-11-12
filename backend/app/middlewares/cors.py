"""Configuración de CORS para que el frontend pueda consumir la API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings


def configurar_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origenes,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
