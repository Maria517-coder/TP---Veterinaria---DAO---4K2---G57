"""Red de clínicas veterinarias (hay una sola)."""
from __future__ import annotations

from sqlalchemy import Index, String, literal_column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


INDICE_RED_UNICA = Index(
    "uq_red_veterinaria_unica", literal_column("(1)"), unique=True
)


class RedVeterinaria(Base):
    """Única red que agrupa todas las clínicas del sistema."""

    __tablename__ = "red_veterinaria"
    __table_args__ = (INDICE_RED_UNICA,)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))

    clinicas: Mapped[list["ClinicaVeterinaria"]] = relationship(back_populates="red")

    def agregar_clinica(self, clinica: "ClinicaVeterinaria") -> None:
        raise NotImplementedError("TODO: agregar la clínica a la red")
