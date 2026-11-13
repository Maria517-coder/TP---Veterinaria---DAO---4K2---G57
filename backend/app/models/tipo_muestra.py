"""Tipo de muestra biológica y su costo de análisis."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.config.database import Base
from app.models.importes import normalizar_importe


class TipoMuestra(Base):
    __tablename__ = "tipo_muestra"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    costo_analisis: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), default=Decimal("0.00")
    )

    @validates("costo_analisis")
    def _normalizar_costo_analisis(self, _clave: str, valor: Decimal | str | int) -> Decimal:
        """Normaliza el costo tanto al crear como al modificar el tipo."""
        return normalizar_importe(valor)
