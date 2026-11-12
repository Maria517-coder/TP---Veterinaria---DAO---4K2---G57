"""Contenedor de envío: la parte FÍSICA del envío (precinto y muestras que transporta)."""
from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


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
        raise NotImplementedError(
            "TODO: solo muestras Extraida y de la misma clínica de origen; pasan a Empaquetada"
        )

    def generar_remito(self, laboratorio_destino: str) -> "RemitoBiologico":
        raise NotImplementedError("TODO: exigir al menos una muestra y crear el remito en estado GENERADO")

    def romper_precinto(self) -> None:
        raise NotImplementedError("TODO: precinto_intacto = False (sin vuelta atrás)")

    def todas_muestras_finalizadas(self) -> bool:
        raise NotImplementedError("TODO: true si todas las muestras están Analizada o Rechazada")
