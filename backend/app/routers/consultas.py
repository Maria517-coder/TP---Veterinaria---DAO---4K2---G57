"""Rutas del módulo Consultas y derivación."""
from fastapi import APIRouter

router = APIRouter(prefix="/consultas", tags=["Consultas"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO POST /consultas  (ConsultaMedica (alta))
# TODO GET /consultas
# TODO GET /consultas/{id}
# TODO POST /consultas/{id}/muestras  (ConsultaMedica.registrarMuestra())
# TODO GET /consultas/{id}/muestras
# TODO GET /consultas/{id}/orden-derivacion  (ConsultaMedica.emitirOrdenDerivacion())
# TODO GET /consultas/{id}/comprobante  (ConsultaMedica.imprimirComprobante())
# TODO GET /consultas/{id}/costo-total  (ConsultaMedica.costoTotal())
