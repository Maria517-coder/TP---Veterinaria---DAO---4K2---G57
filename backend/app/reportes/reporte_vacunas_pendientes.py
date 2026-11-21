"""Reporte de vacunas pendientes."""
from app.models.mascota import Mascota
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


class ReporteVacunasPendientes(Reporte):
    """Snapshot de obligatorias no aplicadas; no tiene fecha natural de filtro."""

    NOMBRES_TOTALES = ("mascotas_con_pendientes", "vacunas_pendientes")

    def __init__(self, repositorio: ReporteRepository) -> None:
        self.repositorio = repositorio

    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Trae las mascotas activas (con clínica, si se pidió una)."""
        # Las fechas del filtro no se aplican: esto es un snapshot, no un período.
        return self.repositorio.listar_mascotas(filtro)

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Reutiliza historia_clinica.vacunas_pendientes() para cada mascota."""
        filas: list[dict[str, object]] = []
        total_vacunas = 0

        for dato in datos:
            if not isinstance(dato, Mascota):
                continue
            pendientes = dato.historia_clinica.vacunas_pendientes()
            if not pendientes:
                continue
            nombres = [vacuna.nombre for vacuna in pendientes]
            filas.append({
                "mascota_id": dato.id,
                "mascota": dato.nombre,
                "especie": dato.especie.nombre,
                "vacunas_pendientes": nombres,
                "cantidad": len(nombres),
            })
            total_vacunas += len(nombres)

        return ResultadoReporte(
            titulo="Vacunas obligatorias pendientes por mascota",
            filas=filas,
            totales=[len(filas), total_vacunas],
        )
