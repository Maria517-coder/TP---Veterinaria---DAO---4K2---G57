"""Vacuna del catálogo y su tabla intermedia con las especies a las que aplica."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base

vacuna_especie = Table(
    "vacuna_especie",
    Base.metadata,
    Column("vacuna_id", ForeignKey("vacuna.id"), primary_key=True),
    Column("especie_id", ForeignKey("especie.id"), primary_key=True),
)


class Vacuna(Base):
    __tablename__ = "vacuna"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    obligatoria: Mapped[bool] = mapped_column(Boolean, default=False)

    especies_aplicables: Mapped[list["Especie"]] = relationship(
        secondary=vacuna_especie, back_populates="vacunas"
    )
