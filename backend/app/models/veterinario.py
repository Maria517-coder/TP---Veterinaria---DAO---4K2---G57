"""Veterinario de una clínica."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.agenda import Agenda


class Veterinario(Base):
    __tablename__ = "veterinario"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinica_id: Mapped[int] = mapped_column(ForeignKey("clinica.id"))
    matricula: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))

    clinica: Mapped["ClinicaVeterinaria"] = relationship(back_populates="veterinarios")
    turnos: Mapped[list["Turno"]] = relationship(back_populates="veterinario")

    @property
    def agenda(self) -> Agenda:
        """La agenda es el conjunto de turnos del veterinario (no tiene tabla propia)."""
        return Agenda(self.turnos)
