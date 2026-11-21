"""Casos de uso del módulo Reportes."""
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado
from app.repositories.clinica_repository import ClinicaRepository
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.reporte import Reporte
from app.reportes.reporte_atenciones_derivaciones import ReporteAtencionesDerivaciones
from app.reportes.reporte_facturacion_desglosada import ReporteFacturacionDesglosada
from app.reportes.reporte_muestras_rechazadas import ReporteMuestrasRechazadas
from app.reportes.reporte_tiempos_promedio import ReporteTiemposPromedio
from app.reportes.reporte_vacunas_pendientes import ReporteVacunasPendientes
from app.schemas.reporte import (
    FiltroReporteRequest,
    ReporteRespuesta,
    totales_nombrados,
)


class ReporteService:
    """Orquesta los casos de uso de Reportes y arma la respuesta JSON."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repositorio = ReporteRepository(db)
        self.clinicas = ClinicaRepository(db)

    def facturacion_desglosada(
        self, filtros: FiltroReporteRequest
    ) -> ReporteRespuesta:
        """Genera el desglose de facturación por clínica y laboratorio."""
        filtro = self._crear_filtro(filtros)
        self._validar_clinica(filtro)
        return self._responder(ReporteFacturacionDesglosada(self.repositorio), filtro)

    def atenciones_derivaciones(
        self, filtros: FiltroReporteRequest
    ) -> ReporteRespuesta:
        """E61: atenciones clínicas y consultas que derivaron muestras."""
        filtro = self._crear_filtro(filtros)
        self._validar_clinica(filtro)
        return self._responder(
            ReporteAtencionesDerivaciones(self.repositorio), filtro
        )

    def muestras_rechazadas(
        self, filtros: FiltroReporteRequest
    ) -> ReporteRespuesta:
        """E62: rechazos ocurridos en el período, fechados por el historial."""
        filtro = self._crear_filtro(filtros)
        self._validar_clinica(filtro)
        return self._responder(
            ReporteMuestrasRechazadas(self.repositorio), filtro
        )

    def vacunas_pendientes(
        self, filtros: FiltroReporteRequest
    ) -> ReporteRespuesta:
        """E63: snapshot de vacunas obligatorias aún no aplicadas."""
        filtro = self._crear_filtro(filtros)
        self._validar_clinica(filtro)
        return self._responder(ReporteVacunasPendientes(self.repositorio), filtro)

    def tiempos_promedio(
        self, filtros: FiltroReporteRequest
    ) -> ReporteRespuesta:
        """E65: promedios de tránsito y procesamiento, en segundos."""
        filtro = self._crear_filtro(filtros)
        self._validar_clinica(filtro)
        return self._responder(ReporteTiemposPromedio(self.repositorio), filtro)

    def _crear_filtro(self, filtros: FiltroReporteRequest) -> FiltroReporte:
        """Traduce el schema de entrada al objeto del dominio."""
        return FiltroReporte(
            desde=filtros.desde, hasta=filtros.hasta, clinica_id=filtros.clinica_id
        )

    def _validar_clinica(self, filtro: FiltroReporte) -> None:
        """Una clínica inexistente se traduce a 404 antes de consultar datos."""
        if filtro.clinica_id is not None and (
            self.clinicas.buscar_clinica_por_id(filtro.clinica_id) is None
        ):
            raise RecursoNoEncontrado(f"No existe la clínica {filtro.clinica_id}")

    def _responder(self, reporte: Reporte, filtro: FiltroReporte) -> ReporteRespuesta:
        """Ejecuta la plantilla y convierte los totales a un objeto por nombre."""
        resultado = reporte.generar(filtro)
        return ReporteRespuesta(
            titulo=resultado.titulo,
            filas=resultado.filas,
            totales=totales_nombrados(reporte.NOMBRES_TOTALES, resultado.totales),
        )
