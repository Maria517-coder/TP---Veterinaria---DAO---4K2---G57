"""Tipo de muestra biológica y su costo de análisis."""
from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class TipoMuestra(Base):
    __tablename__ = "tipo_muestra"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    costo_analisis: Mapped[float] = mapped_column(Float, default=0.0)
