"""Consulta médica: de ella pueden surgir muestras biológicas para derivar al laboratorio."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, select
from sqlalchemy.orm import Mapped, mapped_column, object_session, relationship, validates

from app.config.database import Base
from app.models.cambio_estado import CambioEstado
from app.models.complejidad import Complejidad
from app.models.estado_catalogo import EstadoCatalogo
from app.models.importes import normalizar_importe
from app.models.muestra_biologica import MuestraBiologica

if TYPE_CHECKING:
    from app.models.tipo_muestra import TipoMuestra


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
        """Crea la muestra en Extraida con su primer registro de cambio de estado."""
        sesion = object_session(self)
        estado = None
        if sesion is not None:
            estado = sesion.scalar(
                select(EstadoCatalogo).where(EstadoCatalogo.nombre == "Extraida")
            )
        if estado is None:
            estado = EstadoCatalogo(nombre="Extraida")
        muestra = MuestraBiologica(
            consulta=self,
            tipo=tipo,
            estado_actual=estado,
            fecha=self.fecha,
        )
        # back_populates carga las colecciones; la sesión necesita el add explícito
        # (mismo patrón que MuestraBiologica.cambiar_estado).
        registro = CambioEstado(
            muestra=muestra,
            estado=estado,
            fecha_hora=datetime.now(),
            responsable=responsable,
        )
        if sesion is not None:
            sesion.add(muestra)
            sesion.add(registro)
        return muestra

    def tiene_muestras(self) -> bool:
        """Indica si la consulta tiene al menos una muestra."""
        return bool(self.muestras)

    def emitir_orden_derivacion(self) -> bytes:
        """Devuelve la orden de derivación en PDF delegando su presentación."""
        from app.reportes.documentos_consulta import generar_orden_derivacion

        return generar_orden_derivacion(self)

    def imprimir_comprobante(self) -> bytes:
        """Devuelve el comprobante de atención en PDF delegando su presentación."""
        from app.reportes.documentos_consulta import generar_comprobante

        return generar_comprobante(self)

    def costo_total(self) -> Decimal:
        """Suma el costo de atención y el análisis de cada muestra de la consulta."""
        return self.costo + sum(
            (muestra.tipo.costo_analisis for muestra in self.muestras),
            Decimal("0.00"),
        )
