"""Consulta médica: de ella pueden surgir muestras biológicas para derivar al laboratorio."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.config.database import Base
from app.models.complejidad import Complejidad
from app.models.importes import normalizar_importe


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
    costo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), default=Decimal("0.00")
    )

    clinica: Mapped["ClinicaVeterinaria"] = relationship(back_populates="consultas")
    veterinario: Mapped["Veterinario"] = relationship()
    mascota: Mapped["Mascota"] = relationship(back_populates="consultas")
    muestras: Mapped[list["MuestraBiologica"]] = relationship(
        back_populates="consulta", cascade="all, delete-orphan"
    )

    @validates("costo")
    def _normalizar_costo(self, _clave: str, valor: Decimal | str | int) -> Decimal:
        """Normaliza el costo tanto al crear como al modificar la consulta."""
        return normalizar_importe(valor)

    def registrar_muestra(self, tipo: "TipoMuestra", responsable: str) -> "MuestraBiologica":
        raise NotImplementedError("TODO: crear la muestra en estado Extraida y su primer CambioEstado")

    def tiene_muestras(self) -> bool:
        raise NotImplementedError("TODO: indicar si la consulta tiene muestras")

    def emitir_orden_derivacion(self) -> None:
        raise NotImplementedError("TODO: generar la orden de derivación imprimible")

    def imprimir_comprobante(self) -> None:
        raise NotImplementedError("TODO: generar el comprobante de atención imprimible")

    def costo_total(self) -> Decimal:
        """Suma el costo de atención y el análisis de cada muestra de la consulta."""
        return self.costo + sum(
            (muestra.tipo.costo_analisis for muestra in self.muestras),
            Decimal("0.00"),
        )
