"""Clínica veterinaria de la red."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class ClinicaVeterinaria(Base):
    __tablename__ = "clinica"

    id: Mapped[int] = mapped_column(primary_key=True)
    red_id: Mapped[int] = mapped_column(ForeignKey("red_veterinaria.id"))
    nombre: Mapped[str] = mapped_column(String(100))

    red: Mapped["RedVeterinaria"] = relationship(back_populates="clinicas")
    veterinarios: Mapped[list["Veterinario"]] = relationship(back_populates="clinica")
    consultas: Mapped[list["ConsultaMedica"]] = relationship(back_populates="clinica")

    def facturacion_total_clinica(self, desde: date, hasta: date) -> Decimal:
        """Suma las atenciones por fecha de consulta, incluidos ambos límites."""
        return sum(
            (consulta.costo for consulta in self.consultas if desde <= consulta.fecha <= hasta),
            Decimal("0.00"),
        )

    def facturacion_total_laboratorio(self, desde: date, hasta: date) -> Decimal:
        """Suma los análisis por fecha de consulta, incluidos ambos límites."""
        return sum(
            (
                muestra.tipo.costo_analisis
                for consulta in self.consultas
                if desde <= consulta.fecha <= hasta
                for muestra in consulta.muestras
            ),
            Decimal("0.00"),
        )
