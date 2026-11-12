"""Tabla catálogo ESTADO: una fila por cada estado posible de una muestra.

No confundir con la clase abstracta Estado (patrón State, en models/estados/).
"""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class EstadoCatalogo(Base):
    __tablename__ = "estado"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)
