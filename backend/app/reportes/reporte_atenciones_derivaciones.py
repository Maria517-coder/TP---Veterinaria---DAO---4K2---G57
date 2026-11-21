"""Reporte de atenciones clínicas y derivaciones realizadas."""
from app.models.consulta_medica import ConsultaMedica
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteAtencionesDerivaciones(Reporte):
    """Cuenta las consultas del período y cuáles derivaron muestras."""

    NOMBRES_TOTALES = ("atenciones", "derivaciones")

    def __init__(self, repositorio: ReporteRepository) -> None:
        self.repositorio = repositorio

    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Trae las consultas por fecha de atención y clínica."""
        return self.repositorio.listar_consultas(filtro)

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Cada consulta es una atención; se derivó si tiene muestras."""
        filas: list[dict[str, object]] = []
        derivaciones = 0

        for dato in datos:
            if not isinstance(dato, ConsultaMedica):
                continue
            cantidad = len(dato.muestras)
            if cantidad:
                derivaciones += 1
            filas.append({
                "consulta_id": dato.id,
                "numero": dato.numero,
                "fecha": dato.fecha,
                "clinica": dato.clinica.nombre,
                "veterinario": dato.veterinario.nombre,
                "mascota": dato.mascota.nombre,
                "muestras_derivadas": cantidad,
            })

        return ResultadoReporte(
            titulo="Atenciones clínicas y derivaciones realizadas",
            filas=filas,
            totales=[len(filas), derivaciones],
        )
