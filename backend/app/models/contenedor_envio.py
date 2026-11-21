"""Contenedor de envío: la parte FÍSICA del envío (precinto y muestras que transporta)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.exceptions import ConflictoDeRecurso, ReglaDeNegocioViolada
from app.models.estado_remito import EstadoRemito
from app.models.estados import Analizada, Empaquetada, Extraida, Rechazada


class ContenedorEnvio(Base):
    __tablename__ = "contenedor_envio"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(unique=True)
    precinto_intacto: Mapped[bool] = mapped_column(Boolean, default=True)

    muestras: Mapped[list["MuestraBiologica"]] = relationship(back_populates="contenedor")
    remito: Mapped["RemitoBiologico | None"] = relationship(
        back_populates="contenedor", uselist=False, cascade="all, delete-orphan"
    )

    def agregar_muestra(self, muestra: "MuestraBiologica", responsable: str) -> None:
        """Acepta solo muestras Extraida de una única clínica y las pasa a Empaquetada."""
        if self.remito is not None:
            raise ConflictoDeRecurso(
                "No se pueden agregar muestras una vez generado el remito"
            )
        if not self.precinto_intacto:
            raise ConflictoDeRecurso(
                "No se pueden agregar muestras con el precinto roto"
            )
        if not isinstance(muestra.estado, Extraida):
            raise ConflictoDeRecurso("Solo se pueden agregar muestras Extraida")
        if self.muestras and muestra.consulta.clinica_id != self.muestras[0].consulta.clinica_id:
            raise ReglaDeNegocioViolada(
                "Todas las muestras del contenedor deben ser de la misma clínica de origen"
            )
        muestra.contenedor = self
        muestra.cambiar_estado(Empaquetada(), responsable)

    def generar_remito(
        self, laboratorio_destino: str, numero: int
    ) -> "RemitoBiologico":
        """Crea el remito en GENERADO a partir de las muestras ya cargadas."""
        from app.models.remito_biologico import RemitoBiologico

        if not self.muestras:
            raise ConflictoDeRecurso("El contenedor no tiene muestras para generar el remito")
        if self.remito is not None:
            raise ConflictoDeRecurso("El contenedor ya tiene un remito")
        return RemitoBiologico(
            numero=numero,
            fecha_emision=datetime.now(),
            clinica_origen_id=self.muestras[0].consulta.clinica_id,
            laboratorio_destino=laboratorio_destino,
            estado=EstadoRemito.GENERADO,
            contenedor=self,
        )

    def romper_precinto(self) -> None:
        """Deja el precinto roto sin vuelta atrás; prohibido después de la recepción."""
        if not self.precinto_intacto:
            raise ConflictoDeRecurso("El precinto ya está roto")
        if self.remito is not None and self.remito.estado in (
            EstadoRemito.RECIBIDO,
            EstadoRemito.CERRADO,
        ):
            raise ConflictoDeRecurso(
                "No se puede romper el precinto después de la recepción"
            )
        self.precinto_intacto = False

    def todas_muestras_finalizadas(self) -> bool:
        """Indica si todas las muestras están Analizada o Rechazada (y hay al menos una)."""
        if not self.muestras:
            return False
        return all(isinstance(muestra.estado, (Analizada, Rechazada)) for muestra in self.muestras)
