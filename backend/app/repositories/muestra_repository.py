"""Acceso a datos de: Muestra biológica."""
from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.consulta_medica import ConsultaMedica
from app.models.estado_catalogo import EstadoCatalogo
from app.models.muestra_biologica import MuestraBiologica


class MuestraRepository:
    """Consultas y persistencia de: Muestra biológica."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def buscar_por_id(self, muestra_id: int) -> MuestraBiologica | None:
        """Devuelve la muestra con ese id, o None si no existe."""
        return self.db.scalar(
            select(MuestraBiologica).where(MuestraBiologica.id == muestra_id)
        )

    def listar(
        self,
        *,
        estado: str | None = None,
        clinica_id: int | None = None,
        contenedor_id: int | None = None,
        fecha: date | None = None,
    ) -> list[MuestraBiologica]:
        """Lista muestras ordenadas por id, con los filtros dados combinados."""
        consulta: Select[MuestraBiologica] = select(MuestraBiologica)
        if estado is not None:
            consulta = consulta.join(
                EstadoCatalogo, MuestraBiologica.estado_actual_id == EstadoCatalogo.id
            ).where(EstadoCatalogo.nombre == estado)
        if clinica_id is not None:
            consulta = consulta.join(
                ConsultaMedica, MuestraBiologica.consulta_id == ConsultaMedica.id
            ).where(ConsultaMedica.clinica_id == clinica_id)
        if contenedor_id is not None:
            consulta = consulta.where(
                MuestraBiologica.contenedor_id == contenedor_id
            )
        if fecha is not None:
            consulta = consulta.where(MuestraBiologica.fecha == fecha)
        return list(self.db.scalars(consulta.order_by(MuestraBiologica.id)))

    def guardar(self, muestra: MuestraBiologica) -> MuestraBiologica:
        """Agrega o actualiza la muestra en la sesión, sin confirmar la transacción."""
        self.db.add(muestra)
        self.db.flush()
        return muestra
