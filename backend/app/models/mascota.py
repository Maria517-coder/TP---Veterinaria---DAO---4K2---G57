"""Mascota: siempre tiene un responsable (cliente) y una única historia clínica."""
from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Mascota(Base):
    __tablename__ = "mascota"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))  # NOT NULL: responsable obligatorio
    especie_id: Mapped[int] = mapped_column(ForeignKey("especie.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    fecha_nacimiento: Mapped[date]

    responsable: Mapped["Cliente"] = relationship(back_populates="mascotas")
    especie: Mapped["Especie"] = relationship()
    historia_clinica: Mapped["HistoriaClinica"] = relationship(
        back_populates="mascota", uselist=False, cascade="all, delete-orphan"
    )
    consultas: Mapped[list["ConsultaMedica"]] = relationship(back_populates="mascota")
    turnos: Mapped[list["Turno"]] = relationship(back_populates="mascota")
