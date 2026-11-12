"""Registro inmutable de un cambio de estado de una muestra (solo se inserta, nunca se modifica)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class CambioEstado(Base):
    __tablename__ = "cambio_estado"

    id: Mapped[int] = mapped_column(primary_key=True)
    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestra_biologica.id"))
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado.id"))
    fecha_hora: Mapped[datetime]
    responsable: Mapped[str] = mapped_column(String(100))

    muestra: Mapped["MuestraBiologica"] = relationship(back_populates="historial")
    estado: Mapped["EstadoCatalogo"] = relationship()
