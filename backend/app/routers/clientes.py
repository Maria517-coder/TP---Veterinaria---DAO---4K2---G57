"""Rutas del módulo Clientes."""
from fastapi import APIRouter

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO POST /clientes  (Cliente (alta))
# TODO GET /clientes
# TODO GET /clientes/{id}
# TODO PUT /clientes/{id}
# TODO DELETE /clientes/{id}
# TODO GET /clientes/{id}/mascotas
