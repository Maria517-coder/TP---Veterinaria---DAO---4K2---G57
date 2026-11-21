"""Remito biológico: el envío como TRÁMITE (origen, destino, fechas y ciclo de vida)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.exceptions import ConflictoDeRecurso
from app.models.estado_remito import EstadoRemito
from app.models.estados import Empaquetada, EnTransito, Recibida, Rechazada


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

    def imprimir(self) -> bytes:
        """Devuelve el remito biológico imprimible en PDF."""
        from app.reportes.documento_remito import generar_remito

        return generar_remito(self)

    def despachar(self, responsable: str) -> None:
        """Pasa de GENERADO a DESPACHADO y envía las muestras a EnTransito."""
        if self.estado is not EstadoRemito.GENERADO:
            raise ConflictoDeRecurso("Solo se puede despachar un remito GENERADO")
        muestras = list(self.contenedor.muestras)
        if any(not isinstance(muestra.estado, Empaquetada) for muestra in muestras):
            raise ConflictoDeRecurso(
                "Todas las muestras deben estar Empaquetada para despachar"
            )
        self.estado = EstadoRemito.DESPACHADO
        self.fecha_hora_despacho = datetime.now()
        for muestra in muestras:
            muestra.cambiar_estado(EnTransito(), responsable)

    def registrar_recepcion(self, responsable: str) -> None:
        """Pasa de DESPACHADO a RECIBIDO y aplica el efecto del estado del precinto."""
        if self.estado is not EstadoRemito.DESPACHADO:
            raise ConflictoDeRecurso("Solo se puede recepcionar un remito DESPACHADO")
        muestras = list(self.contenedor.muestras)
        if any(not isinstance(muestra.estado, EnTransito) for muestra in muestras):
            raise ConflictoDeRecurso(
                "Todas las muestras deben estar EnTransito para recepcionar"
            )
        # La regla "pasa igual a RECIBIDO" se cumple primero, aunque el precinto esté roto;
        # recién después se encadena el cierre automático si no quedan muestras pendientes.
        self.estado = EstadoRemito.RECIBIDO
        self.fecha_hora_recepcion = datetime.now()
        destino = Recibida() if self.contenedor.precinto_intacto else Rechazada()
        for muestra in muestras:
            muestra.cambiar_estado(destino, responsable)
        if self.contenedor.todas_muestras_finalizadas():
            self.cerrar()

    def cerrar(self) -> None:
        """Pasa a CERRADO; lo llaman la recepción y E47, nunca un endpoint."""
        if self.estado is not EstadoRemito.RECIBIDO:
            raise ConflictoDeRecurso("Solo se puede cerrar un remito RECIBIDO")
        self.estado = EstadoRemito.CERRADO

    def tiempo_transito(self) -> float:
        """Devuelve en segundos la diferencia entre despacho y recepción."""
        if self.fecha_hora_despacho is None or self.fecha_hora_recepcion is None:
            raise ConflictoDeRecurso(
                "El remito todavía no tiene despacho y recepción"
            )
        return (self.fecha_hora_recepcion - self.fecha_hora_despacho).total_seconds()
