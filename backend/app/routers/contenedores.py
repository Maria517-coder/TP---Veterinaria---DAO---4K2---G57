"""Rutas del módulo Contenedores de envío."""
from fastapi import APIRouter

router = APIRouter(prefix="/contenedores", tags=["Contenedores"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO POST /contenedores  (ContenedorEnvio (alta))
# TODO GET /contenedores
# TODO GET /contenedores/{id}
# TODO POST /contenedores/{id}/muestras  (ContenedorEnvio.agregarMuestra())
# TODO POST /contenedores/{id}/romper-precinto  (ContenedorEnvio.romperPrecinto())
# TODO POST /contenedores/{id}/remito  (ContenedorEnvio.generarRemito())
# TODO GET /contenedores/{id}/remito
