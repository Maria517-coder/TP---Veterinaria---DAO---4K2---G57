"""Reporte de atenciones clínicas y derivaciones realizadas."""
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteAtencionesDerivaciones(Reporte):
    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        raise NotImplementedError("TODO: consultar los datos de: atenciones clínicas y derivaciones realizadas")

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        raise NotImplementedError("TODO: calcular el resultado de: atenciones clínicas y derivaciones realizadas")
