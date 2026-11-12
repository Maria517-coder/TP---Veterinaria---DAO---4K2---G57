"""Reporte de muestras rechazadas por fallas en el transporte."""
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteMuestrasRechazadas(Reporte):
    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        raise NotImplementedError("TODO: consultar los datos de: muestras rechazadas por fallas en el transporte")

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        raise NotImplementedError("TODO: calcular el resultado de: muestras rechazadas por fallas en el transporte")
