"""Rutas del módulo Muestras y trazabilidad."""
from fastapi import APIRouter

router = APIRouter(prefix="/muestras", tags=["Muestras"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO GET /muestras
# TODO GET /muestras/{id}
# TODO GET /muestras/{id}/historial-estados  (MuestraBiologica.historial)
# TODO POST /muestras/{id}/resultado  (MuestraBiologica.registrarResultado())
