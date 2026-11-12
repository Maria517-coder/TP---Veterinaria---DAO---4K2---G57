"""Consulta médica: de ella pueden surgir muestras biológicas para derivar al laboratorio."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Enum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.complejidad import Complejidad


class ConsultaMedica(Base):
    __tablename__ = "consulta"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(unique=True)
    clinica_id: Mapped[int] = mapped_column(ForeignKey("clinica.id"))
    veterinario_id: Mapped[int] = mapped_column(ForeignKey("veterinario.id"))
    mascota_id: Mapped[int] = mapped_column(ForeignKey("mascota.id"))
    fecha: Mapped[date]
    complejidad: Mapped[Complejidad] = mapped_column(
        Enum(Complejidad, native_enum=False, create_constraint=True, length=10)
    )
    costo: Mapped[float] = mapped_column(Float, default=0.0)

    clinica: Mapped["ClinicaVeterinaria"] = relationship(back_populates="consultas")
    veterinario: Mapped["Veterinario"] = relationship()
    mascota: Mapped["Mascota"] = relationship(back_populates="consultas")
    muestras: Mapped[list["MuestraBiologica"]] = relationship(
        back_populates="consulta", cascade="all, delete-orphan"
    )

    def registrar_muestra(self, tipo: "TipoMuestra", responsable: str) -> "MuestraBiologica":
        raise NotImplementedError("TODO: crear la muestra en estado Extraida y su primer CambioEstado")

    def tiene_muestras(self) -> bool:
        raise NotImplementedError("TODO: indicar si la consulta tiene muestras")

    def emitir_orden_derivacion(self) -> None:
        raise NotImplementedError("TODO: generar la orden de derivación imprimible")

    def imprimir_comprobante(self) -> None:
        raise NotImplementedError("TODO: generar el comprobante de atención imprimible")

    def costo_total(self) -> float:
        raise NotImplementedError("TODO: costo de la consulta más el costo de análisis de sus muestras")
