"""Reporte de tiempo promedio de tránsito y de procesamiento."""
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteTiemposPromedio(Reporte):
    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        raise NotImplementedError("TODO: consultar los datos de: tiempo promedio de tránsito y de procesamiento")

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        raise NotImplementedError("TODO: calcular el resultado de: tiempo promedio de tránsito y de procesamiento")
