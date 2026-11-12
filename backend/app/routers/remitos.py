"""Rutas del módulo Remitos biológicos."""
from fastapi import APIRouter

router = APIRouter(prefix="/remitos", tags=["Remitos"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO GET /remitos
# TODO GET /remitos/{id}
# TODO GET /remitos/{id}/imprimir  (RemitoBiologico.imprimir())
# TODO POST /remitos/{id}/despachar  (RemitoBiologico.despachar())
# TODO POST /remitos/{id}/recepcion  (RemitoBiologico.registrarRecepcion())
# TODO GET /remitos/{id}/tiempo-transito  (RemitoBiologico.tiempoTransito())
