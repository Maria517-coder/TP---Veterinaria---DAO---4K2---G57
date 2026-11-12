"""Red de clínicas veterinarias (hay una sola)."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class RedVeterinaria(Base):
    __tablename__ = "red_veterinaria"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))

    clinicas: Mapped[list["ClinicaVeterinaria"]] = relationship(back_populates="red")

    def agregar_clinica(self, clinica: "ClinicaVeterinaria") -> None:
        raise NotImplementedError("TODO: agregar la clínica a la red")
