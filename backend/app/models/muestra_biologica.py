"""Muestra biológica: su ciclo de vida usa el patrón State y su historial es inmutable."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship

from app.config.database import Base
from app.exceptions import ReglaDeNegocioViolada, TransicionInvalida
from app.models.cambio_estado import CambioEstado
from app.models.estado_catalogo import EstadoCatalogo
from app.models.estados import Recibida, estado_desde_nombre
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
        cascade="save-update, merge",
        passive_deletes="all",
        order_by="CambioEstado.fecha_hora",
    )

    @property
    def estado(self) -> Estado:
        """Objeto del patrón State que corresponde al estado guardado en la base."""
        return estado_desde_nombre(self.estado_actual.nombre)

    def cambiar_estado(self, nuevo: Estado, responsable: str) -> None:
        """Valida la transición, actualiza el estado y deja registrado el cambio."""
        actual = self.estado
        if not actual.puede_pasar_a(nuevo):
            raise TransicionInvalida(
                f"No se puede pasar de {actual.nombre} a {nuevo.nombre}"
            )

        sesion = object_session(self)
        if sesion is None:
            raise ReglaDeNegocioViolada(
                "La muestra no tiene sesión: debe estar persistida para registrar el cambio"
            )
        destino = sesion.scalar(
            select(EstadoCatalogo).where(EstadoCatalogo.nombre == nuevo.nombre)
        )
        if destino is None:
            raise ReglaDeNegocioViolada(
                f"No existe el estado {nuevo.nombre} en el catálogo"
            )

        self.estado_actual = destino
        registro = CambioEstado(
            muestra=self,
            estado=destino,
            fecha_hora=datetime.now(),
            responsable=responsable,
        )
        # back_populates carga self.historial; la sesión necesita el add explícito.
        sesion.add(registro)

    def registrar_resultado(self, texto: str, responsable: str) -> None:
        raise NotImplementedError(
            "TODO: exigir puede_procesarse(), guardar el resultado, pasar a Analizada y cerrar el remito si corresponde"
        )

    def puede_procesarse(self) -> bool:
        """Solo se procesa una muestra Recibida, es decir, con precinto intacto."""
        return isinstance(self.estado, Recibida)

    def tiempo_procesamiento(self) -> float:
        raise NotImplementedError("TODO: diferencia entre los registros Recibida y Analizada del historial")
