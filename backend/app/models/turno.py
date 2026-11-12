"""Turno de un veterinario para una mascota."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Turno(Base):
    __tablename__ = "turno"

    id: Mapped[int] = mapped_column(primary_key=True)
    veterinario_id: Mapped[int] = mapped_column(ForeignKey("veterinario.id"))
    mascota_id: Mapped[int] = mapped_column(ForeignKey("mascota.id"))
    inicio: Mapped[datetime]
    fin: Mapped[datetime]

    veterinario: Mapped["Veterinario"] = relationship(back_populates="turnos")
    mascota: Mapped["Mascota"] = relationship(back_populates="turnos")
