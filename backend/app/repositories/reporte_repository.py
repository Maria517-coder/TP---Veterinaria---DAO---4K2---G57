"""Acceso a datos de solo lectura para los cinco reportes."""
from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cambio_estado import CambioEstado
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.consulta_medica import ConsultaMedica
from app.models.estado_catalogo import EstadoCatalogo
from app.models.mascota import Mascota
from app.models.muestra_biologica import MuestraBiologica
from app.models.remito_biologico import RemitoBiologico

if TYPE_CHECKING:
    from app.reportes.filtro_reporte import FiltroReporte


class ReporteRepository:
    """Consultas de los reportes: devuelve entidades y nunca confirma."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def listar_clinicas(
        self, clinica_id: int | None = None
    ) -> list[ClinicaVeterinaria]:
        """Lista las clínicas, opcionalmente reducidas a un id."""
        consulta = select(ClinicaVeterinaria)
        if clinica_id is not None:
            consulta = consulta.where(ClinicaVeterinaria.id == clinica_id)
        return list(
            self.db.scalars(
                consulta.order_by(ClinicaVeterinaria.nombre, ClinicaVeterinaria.id)
            )
        )

    def buscar_clinica_por_id(self, clinica_id: int) -> ClinicaVeterinaria | None:
        """Devuelve la clínica con ese id, o None si no existe."""
        return self.db.get(ClinicaVeterinaria, clinica_id)

    def listar_consultas(self, filtro: FiltroReporte) -> list[ConsultaMedica]:
        """Consultas por fecha, con rango inclusivo y filtro opcional de clínica."""
        consulta = select(ConsultaMedica)
        if filtro.desde is not None:
            consulta = consulta.where(ConsultaMedica.fecha >= filtro.desde)
        if filtro.hasta is not None:
            consulta = consulta.where(ConsultaMedica.fecha <= filtro.hasta)
        if filtro.clinica_id is not None:
            consulta = consulta.where(ConsultaMedica.clinica_id == filtro.clinica_id)
        return list(
            self.db.scalars(
                consulta.order_by(ConsultaMedica.fecha, ConsultaMedica.id)
            )
        )

    def listar_cambios_a_rechazada(
        self, filtro: FiltroReporte
    ) -> list[CambioEstado]:
        """Registros del paso a Rechazada, fechados por el cambio de estado."""
        consulta = (
            select(CambioEstado)
            .join(CambioEstado.estado)
            .where(EstadoCatalogo.nombre == "Rechazada")
        )
        if filtro.desde is not None:
            consulta = consulta.where(
                func.date(CambioEstado.fecha_hora) >= filtro.desde
            )
        if filtro.hasta is not None:
            consulta = consulta.where(
                func.date(CambioEstado.fecha_hora) <= filtro.hasta
            )
        if filtro.clinica_id is not None:
            consulta = (
                consulta.join(CambioEstado.muestra)
                .join(MuestraBiologica.consulta)
                .where(ConsultaMedica.clinica_id == filtro.clinica_id)
            )
        return list(self.db.scalars(consulta.order_by(CambioEstado.fecha_hora)))

    def listar_mascotas(self, filtro: FiltroReporte) -> list[Mascota]:
        """Mascotas activas; con clínica, solo las que tienen consultas allí."""
        consulta = select(Mascota).where(Mascota.activo.is_(True))
        if filtro.clinica_id is not None:
            consulta = (
                consulta.join(Mascota.consultas)
                .where(ConsultaMedica.clinica_id == filtro.clinica_id)
                .distinct()
            )
        return list(self.db.scalars(consulta.order_by(Mascota.id)))

    def listar_remitos_despachados(
        self, filtro: FiltroReporte
    ) -> list[RemitoBiologico]:
        """Remitos despachados, fechados por fecha_hora_despacho."""
        consulta = select(RemitoBiologico).where(
            RemitoBiologico.fecha_hora_despacho.is_not(None)
        )
        if filtro.desde is not None:
            consulta = consulta.where(
                RemitoBiologico.fecha_hora_despacho
                >= datetime.combine(filtro.desde, time.min)
            )
        if filtro.hasta is not None:
            consulta = consulta.where(
                RemitoBiologico.fecha_hora_despacho
                <= datetime.combine(filtro.hasta, time.max)
            )
        if filtro.clinica_id is not None:
            consulta = consulta.where(
                RemitoBiologico.clinica_origen_id == filtro.clinica_id
            )
        return list(self.db.scalars(consulta.order_by(RemitoBiologico.id)))
