"""Rutas del módulo Reportes."""
from fastapi import APIRouter

router = APIRouter(prefix="/reportes", tags=["Reportes"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO GET /reportes/atenciones-derivaciones  (ReporteAtencionesDerivaciones)
# TODO GET /reportes/muestras-rechazadas  (ReporteMuestrasRechazadas)
# TODO GET /reportes/vacunas-pendientes  (ReporteVacunasPendientes)
# TODO GET /reportes/facturacion  (ReporteFacturacionDesglosada)
# TODO GET /reportes/tiempos-promedio  (ReporteTiemposPromedio)
