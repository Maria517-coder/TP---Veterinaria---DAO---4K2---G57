"""Aplicación de una vacuna a una mascota (hecho registrado en su historia clínica)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class AplicacionVacuna(Base):
    __tablename__ = "aplicacion_vacuna"

    id: Mapped[int] = mapped_column(primary_key=True)
    historia_clinica_id: Mapped[int] = mapped_column(ForeignKey("historia_clinica.id"))
    vacuna_id: Mapped[int] = mapped_column(ForeignKey("vacuna.id"))
    fecha: Mapped[date]

    historia_clinica: Mapped["HistoriaClinica"] = relationship(back_populates="aplicaciones")
    vacuna: Mapped["Vacuna"] = relationship()
