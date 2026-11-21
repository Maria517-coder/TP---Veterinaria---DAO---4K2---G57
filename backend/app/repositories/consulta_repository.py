"""Acceso a datos de: Consulta médica."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.consulta_medica import ConsultaMedica
from app.models.muestra_biologica import MuestraBiologica


class ConsultaRepository:
    """Consultas y persistencia de: Consulta médica."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def siguiente_numero(self) -> int:
        """Devuelve el próximo número correlativo, sin reservarlo todavía."""
        mayor = self.db.scalar(select(func.max(ConsultaMedica.numero)))
        return (mayor or 0) + 1

    def buscar_por_id(self, consulta_id: int) -> ConsultaMedica | None:
        """Busca una consulta por id; devuelve None si no existe."""
        return self.db.get(ConsultaMedica, consulta_id)

    def listar(
        self,
        clinica_id: int | None = None,
        fecha: date | None = None,
        mascota_id: int | None = None,
        veterinario_id: int | None = None,
        con_muestras: bool | None = None,
    ) -> list[ConsultaMedica]:
        """Lista consultas con los filtros combinados, ordenadas por número."""
        consulta = select(ConsultaMedica)
        if clinica_id is not None:
            consulta = consulta.where(ConsultaMedica.clinica_id == clinica_id)
        if fecha is not None:
            consulta = consulta.where(ConsultaMedica.fecha == fecha)
        if mascota_id is not None:
            consulta = consulta.where(ConsultaMedica.mascota_id == mascota_id)
        if veterinario_id is not None:
            consulta = consulta.where(ConsultaMedica.veterinario_id == veterinario_id)
        if con_muestras is not None:
            existe = ConsultaMedica.muestras.any()
            consulta = consulta.where(existe if con_muestras else ~existe)
        return list(self.db.scalars(consulta.order_by(ConsultaMedica.numero)))

    def guardar(self, consulta: ConsultaMedica) -> ConsultaMedica:
        """Agrega o actualiza la consulta en la sesión, sin confirmar la transacción."""
        self.db.add(consulta)
        self.db.flush()
        return consulta

    def guardar_muestra(self, muestra: MuestraBiologica) -> MuestraBiologica:
        """Agrega o actualiza la muestra en la sesión, sin confirmar la transacción."""
        self.db.add(muestra)
        self.db.flush()
        return muestra
