"""Reporte de muestras rechazadas por fallas en el transporte."""
from app.models.cambio_estado import CambioEstado
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteMuestrasRechazadas(Reporte):
    """Lista los rechazos fechados por el cambio al estado Rechazada."""

    NOMBRES_TOTALES = ("muestras_rechazadas",)

    def __init__(self, repositorio: ReporteRepository) -> None:
        self.repositorio = repositorio

    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Trae del historial inmutable los cambios a Rechazada del período."""
        return self.repositorio.listar_cambios_a_rechazada(filtro)

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Una fila por rechazo con la clínica y la consulta de origen."""
        filas: list[dict[str, object]] = []

        for dato in datos:
            if not isinstance(dato, CambioEstado):
                continue
            muestra = dato.muestra
            consulta = muestra.consulta
            filas.append({
                "fecha": dato.fecha_hora.date(),
                "muestra_id": muestra.id,
                "tipo": muestra.tipo.nombre,
                "consulta_numero": consulta.numero,
                "clinica": consulta.clinica.nombre,
                "responsable": dato.responsable,
            })

        return ResultadoReporte(
            titulo="Muestras rechazadas por fallas en el transporte",
            filas=filas,
            totales=[len(filas)],
        )
