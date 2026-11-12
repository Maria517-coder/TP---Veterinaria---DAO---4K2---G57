"""Muestra biológica: su ciclo de vida usa el patrón State y su historial es inmutable."""
from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.estados import estado_desde_nombre
from app.models.estados.estado import Estado


class MuestraBiologica(Base):
    __tablename__ = "muestra_biologica"

    id: Mapped[int] = mapped_column(primary_key=True)
    consulta_id: Mapped[int] = mapped_column(ForeignKey("consulta.id"))
    tipo_muestra_id: Mapped[int] = mapped_column(ForeignKey("tipo_muestra.id"))
    contenedor_id: Mapped[int | None] = mapped_column(ForeignKey("contenedor_envio.id"))
    estado_actual_id: Mapped[int] = mapped_column(ForeignKey("estado.id"))
    fecha: Mapped[date]
    resultado: Mapped[str | None] = mapped_column(String(500))
    fecha_resultado: Mapped[date | None]

    consulta: Mapped["ConsultaMedica"] = relationship(back_populates="muestras")
    tipo: Mapped["TipoMuestra"] = relationship()
    contenedor: Mapped["ContenedorEnvio | None"] = relationship(back_populates="muestras")
    estado_actual: Mapped["EstadoCatalogo"] = relationship()
    historial: Mapped[list["CambioEstado"]] = relationship(
        back_populates="muestra",
        cascade="all, delete-orphan",
        order_by="CambioEstado.fecha_hora",
    )

    @property
    def estado(self) -> Estado:
        """Objeto del patrón State que corresponde al estado guardado en la base."""
        return estado_desde_nombre(self.estado_actual.nombre)

    def cambiar_estado(self, nuevo: Estado, responsable: str) -> None:
        raise NotImplementedError(
            "TODO: validar con estado.puede_pasar_a(nuevo), agregar el CambioEstado y actualizar el estado"
        )

    def registrar_resultado(self, texto: str, responsable: str) -> None:
        raise NotImplementedError(
            "TODO: exigir puede_procesarse(), guardar el resultado, pasar a Analizada y cerrar el remito si corresponde"
        )

    def puede_procesarse(self) -> bool:
        raise NotImplementedError("TODO: true si la muestra está Recibida (llegó con precinto intacto)")

    def tiempo_procesamiento(self) -> float:
        raise NotImplementedError("TODO: diferencia entre los registros Recibida y Analizada del historial")
