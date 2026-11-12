"""Remito biológico: el envío como TRÁMITE (origen, destino, fechas y ciclo de vida)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.estado_remito import EstadoRemito


class RemitoBiologico(Base):
    __tablename__ = "remito_biologico"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(unique=True)
    fecha_emision: Mapped[datetime]
    clinica_origen_id: Mapped[int] = mapped_column(ForeignKey("clinica.id"))
    laboratorio_destino: Mapped[str] = mapped_column(String(100))
    estado: Mapped[EstadoRemito] = mapped_column(
        Enum(EstadoRemito, native_enum=False, create_constraint=True, length=12),
        default=EstadoRemito.GENERADO,
    )
    fecha_hora_despacho: Mapped[datetime | None]
    fecha_hora_recepcion: Mapped[datetime | None]
    contenedor_id: Mapped[int] = mapped_column(ForeignKey("contenedor_envio.id"), unique=True)

    clinica_origen: Mapped["ClinicaVeterinaria"] = relationship()
    contenedor: Mapped["ContenedorEnvio"] = relationship(back_populates="remito")

    def imprimir(self) -> None:
        raise NotImplementedError("TODO: generar el remito biológico imprimible")

    def despachar(self, responsable: str) -> None:
        raise NotImplementedError("TODO: GENERADO a DESPACHADO; guardar fecha_hora_despacho; muestras a EnTransito")

    def registrar_recepcion(self, responsable: str) -> None:
        raise NotImplementedError(
            "TODO: DESPACHADO a RECIBIDO; precinto intacto: muestras Recibida, roto: Rechazada; "
            "si todas quedan finalizadas, llamar a cerrar()"
        )

    def cerrar(self) -> None:
        raise NotImplementedError(
            "TODO: pasar a CERRADO; se llama sola cuando todas las muestras están Analizada o Rechazada"
        )

    def tiempo_transito(self) -> float:
        raise NotImplementedError("TODO: fecha_hora_recepcion menos fecha_hora_despacho")
