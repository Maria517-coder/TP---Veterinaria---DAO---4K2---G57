"""Acceso a datos de: Contenedor de envío."""
from datetime import date

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models.contenedor_envio import ContenedorEnvio
from app.models.muestra_biologica import MuestraBiologica
from app.models.remito_biologico import RemitoBiologico


class ContenedorRepository:
    """Consultas y persistencia de: Contenedor de envío."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def siguiente_numero(self) -> int:
        """Devuelve el próximo número correlativo, sin reservarlo todavía."""
        mayor = self.db.scalar(select(func.max(ContenedorEnvio.numero)))
        return (mayor or 0) + 1

    def buscar_por_id(self, contenedor_id: int) -> ContenedorEnvio | None:
        """Busca un contenedor por id; devuelve None si no existe."""
        return self.db.get(ContenedorEnvio, contenedor_id)

    def listar(
        self,
        *,
        con_remito: bool | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[ContenedorEnvio]:
        """Lista contenedores por id, con filtros combinables de remito y fechas."""
        consulta = select(ContenedorEnvio)
        remito_existe = exists().where(RemitoBiologico.contenedor_id == ContenedorEnvio.id)
        if con_remito is True:
            consulta = consulta.where(remito_existe)
        elif con_remito is False:
            consulta = consulta.where(~remito_existe)
        if desde is not None:
            consulta = consulta.where(
                ContenedorEnvio.muestras.any(MuestraBiologica.fecha >= desde)
            )
        if hasta is not None:
            consulta = consulta.where(
                ContenedorEnvio.muestras.any(MuestraBiologica.fecha <= hasta)
            )
        return list(self.db.scalars(consulta.order_by(ContenedorEnvio.id)))

    def guardar(self, contenedor: ContenedorEnvio) -> ContenedorEnvio:
        """Agrega o actualiza el contenedor en la sesión, sin confirmar la transacción."""
        self.db.add(contenedor)
        self.db.flush()
        return contenedor
