"""Clínica veterinaria de la red."""
from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class ClinicaVeterinaria(Base):
    __tablename__ = "clinica"

    id: Mapped[int] = mapped_column(primary_key=True)
    red_id: Mapped[int] = mapped_column(ForeignKey("red_veterinaria.id"))
    nombre: Mapped[str] = mapped_column(String(100))

    red: Mapped["RedVeterinaria"] = relationship(back_populates="clinicas")
    veterinarios: Mapped[list["Veterinario"]] = relationship(back_populates="clinica")
    consultas: Mapped[list["ConsultaMedica"]] = relationship(back_populates="clinica")

    def facturacion_total_clinica(self, desde: date, hasta: date) -> float:
        raise NotImplementedError("TODO: sumar el costo de las consultas del período")

    def facturacion_total_laboratorio(self, desde: date, hasta: date) -> float:
        raise NotImplementedError("TODO: sumar el costo de análisis de las muestras del período")
