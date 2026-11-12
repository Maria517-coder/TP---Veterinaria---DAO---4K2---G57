"""Cliente: responsable de una o más mascotas."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    telefono: Mapped[str] = mapped_column(String(30))

    mascotas: Mapped[list["Mascota"]] = relationship(back_populates="responsable")
