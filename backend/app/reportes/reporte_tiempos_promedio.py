"""Reporte de tiempo promedio de tránsito y de procesamiento."""
from app.models.muestra_biologica import MuestraBiologica
from app.models.remito_biologico import RemitoBiologico
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteTiemposPromedio(Reporte):
    """Promedios en segundos de remitos filtrados por fecha_hora_despacho."""

    NOMBRES_TOTALES = (
        "tiempo_transito_promedio_segundos",
        "tiempo_procesamiento_promedio_segundos",
    )

    def __init__(self, repositorio: ReporteRepository) -> None:
        self.repositorio = repositorio

    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Trae los remitos despachados en el período y la clínica pedida."""
        return self.repositorio.listar_remitos_despachados(filtro)

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Promedia tránsito por remito y procesamiento por muestra."""
        filas: list[dict[str, object]] = []
        transitos: list[float] = []
        procesamientos: list[float] = []

        for dato in datos:
            if not isinstance(dato, RemitoBiologico):
                continue
            transito = self._transito(dato)
            if transito is not None:
                transitos.append(transito)
            tiempos_muestras = [
                muestra.tiempo_procesamiento()
                for muestra in dato.contenedor.muestras
                if self._procesada(muestra)
            ]
            procesamientos.extend(tiempos_muestras)
            filas.append({
                "remito_id": dato.id,
                "numero": dato.numero,
                "clinica": dato.clinica_origen.nombre,
                "fecha_despacho": dato.fecha_hora_despacho,
                "tiempo_transito_promedio_segundos": transito or 0.0,
                "tiempo_procesamiento_promedio_segundos": (
                    self._promedio(tiempos_muestras)
                ),
            })

        return ResultadoReporte(
            titulo="Tiempos promedio de tránsito y procesamiento (segundos)",
            filas=filas,
            totales=[self._promedio(transitos), self._promedio(procesamientos)],
        )

    @staticmethod
    def _transito(remito: RemitoBiologico) -> float | None:
        """Segundos entre despacho y recepción; None si aún no se recibió."""
        if remito.fecha_hora_despacho is None or remito.fecha_hora_recepcion is None:
            return None
        return (remito.fecha_hora_recepcion - remito.fecha_hora_despacho).total_seconds()

    @staticmethod
    def _procesada(muestra: MuestraBiologica) -> bool:
        """Solo se promedia una muestra que pasó por Recibida y Analizada."""
        nombres = {registro.estado.nombre for registro in muestra.historial}
        return {"Recibida", "Analizada"} <= nombres

    @staticmethod
    def _promedio(valores: list[float]) -> float:
        """Devuelve el promedio en segundos, o 0.0 cuando no hay valores."""
        return round(sum(valores) / len(valores), 2) if valores else 0.0
