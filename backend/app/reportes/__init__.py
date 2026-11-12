"""Reportes (patrón Template Method)."""
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.reporte_atenciones_derivaciones import ReporteAtencionesDerivaciones
from app.reportes.reporte_facturacion_desglosada import ReporteFacturacionDesglosada
from app.reportes.reporte_muestras_rechazadas import ReporteMuestrasRechazadas
from app.reportes.reporte_tiempos_promedio import ReporteTiemposPromedio
from app.reportes.reporte_vacunas_pendientes import ReporteVacunasPendientes
from app.reportes.resultado_reporte import ResultadoReporte

__all__ = [
    "FiltroReporte", "Reporte", "ResultadoReporte",
    "ReporteAtencionesDerivaciones", "ReporteFacturacionDesglosada",
    "ReporteMuestrasRechazadas", "ReporteTiemposPromedio", "ReporteVacunasPendientes",
]
