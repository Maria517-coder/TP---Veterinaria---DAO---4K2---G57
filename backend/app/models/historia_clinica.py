"""Historia clínica de una mascota (relación 1 a 1)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.aplicacion_vacuna import AplicacionVacuna


class HistoriaClinica(Base):
    __tablename__ = "historia_clinica"

    id: Mapped[int] = mapped_column(primary_key=True)
    mascota_id: Mapped[int] = mapped_column(ForeignKey("mascota.id"), unique=True)
    numero: Mapped[int] = mapped_column(unique=True)

    mascota: Mapped["Mascota"] = relationship(back_populates="historia_clinica")
    aplicaciones: Mapped[list["AplicacionVacuna"]] = relationship(
        back_populates="historia_clinica", cascade="all, delete-orphan"
    )

    @property
    def consultas(self) -> list["ConsultaMedica"]:
        """Las consultas se alcanzan a través de la mascota."""
        return self.mascota.consultas

    def registrar_vacunacion(self, vacuna: "Vacuna", fecha: date) -> None:
        """Agrega a la historia el hecho de aplicación de una vacuna."""
        self.aplicaciones.append(AplicacionVacuna(vacuna=vacuna, fecha=fecha))

    def vacunas_pendientes(self) -> list["Vacuna"]:
        """Devuelve las obligatorias de la especie que aún no fueron aplicadas."""
        aplicadas = {aplicacion.vacuna for aplicacion in self.aplicaciones}
        return [
            vacuna for vacuna in self.mascota.especie.vacunas
            if vacuna.obligatoria and vacuna not in aplicadas
        ]

    def imprimir_carnet_vacunas(self) -> None:
        raise NotImplementedError("TODO: generar el carnet de vacunas imprimible")
