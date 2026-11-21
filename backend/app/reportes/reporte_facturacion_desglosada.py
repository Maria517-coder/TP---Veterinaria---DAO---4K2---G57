"""Reporte de facturación desglosada por clínica y laboratorio."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.resultado_reporte import ResultadoReporte


@dataclass(frozen=True)
class _DatosClinica:
    """Pasa el rango al paso de cálculo sin acoplar la clínica al filtro."""

    clinica: ClinicaVeterinaria
    desde: date
    hasta: date


class ReporteFacturacionDesglosada(Reporte):
    """Reutiliza la facturación del modelo: no reimplementa sumas."""

    NOMBRES_TOTALES = ("atenciones", "analisis", "total")

    def __init__(self, repositorio: ReporteRepository) -> None:
        self.repositorio = repositorio

    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Trae las clínicas del filtro junto con el rango a facturar."""
        desde = filtro.desde or date.min
        hasta = filtro.hasta or date.max
        clinicas = dict.fromkeys(
            consulta.clinica
            for consulta in self.repositorio.listar_consultas(filtro)
        )
        return [_DatosClinica(clinica, desde, hasta) for clinica in clinicas]

    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Desglosa atenciones y análisis por clínica y suma ambos totales."""
        filas: list[dict[str, object]] = []
        total_atenciones = Decimal("0.00")
        total_analisis = Decimal("0.00")

        for dato in datos:
            if not isinstance(dato, _DatosClinica):
                continue
            atenciones = dato.clinica.facturacion_total_clinica(
                dato.desde, dato.hasta
            )
            analisis = dato.clinica.facturacion_total_laboratorio(
                dato.desde, dato.hasta
            )
            filas.append({
                "clinica_id": dato.clinica.id,
                "clinica": dato.clinica.nombre,
                "atenciones": atenciones,
                "analisis": analisis,
                "total": atenciones + analisis,
            })
            total_atenciones += atenciones
            total_analisis += analisis

        return ResultadoReporte(
            titulo="Facturación desglosada por clínica y laboratorio",
            filas=filas,
            totales=[total_atenciones, total_analisis, total_atenciones + total_analisis],
        )
