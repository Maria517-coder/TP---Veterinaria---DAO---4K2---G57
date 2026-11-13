"""Registro inmutable de un cambio de estado de una muestra (solo se inserta, nunca se modifica)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, MetaData, String, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class CambioEstado(Base):
    """Hecho histórico que, una vez insertado, no se modifica ni se elimina."""

    __tablename__ = "cambio_estado"

    id: Mapped[int] = mapped_column(primary_key=True)
    muestra_id: Mapped[int] = mapped_column(ForeignKey("muestra_biologica.id"))
    estado_id: Mapped[int] = mapped_column(ForeignKey("estado.id"))
    fecha_hora: Mapped[datetime]
    responsable: Mapped[str] = mapped_column(String(100))

    muestra: Mapped["MuestraBiologica"] = relationship(back_populates="historial")
    estado: Mapped["EstadoCatalogo"] = relationship()


@event.listens_for(Base.metadata, "after_create")
def _proteger_historial(
    _metadata: MetaData, conexion: Connection, **_opciones: object,
) -> None:
    """Instala protección SQLite incluso si create_all encuentra tablas existentes."""
    if conexion.dialect.name != "sqlite":
        return

    for operacion in ("UPDATE", "DELETE"):
        conexion.exec_driver_sql(f"""
            CREATE TRIGGER IF NOT EXISTS cambio_estado_no_{operacion.lower()}
            BEFORE {operacion} ON cambio_estado
            BEGIN
                SELECT RAISE(ABORT, 'historial inmutable');
            END
        """)

    # REPLACE puede borrar sin disparar DELETE si recursive_triggers está desactivado.
    conexion.exec_driver_sql("""
        CREATE TRIGGER IF NOT EXISTS cambio_estado_no_reemplazo
        BEFORE INSERT ON cambio_estado
        WHEN EXISTS (SELECT 1 FROM cambio_estado WHERE id = NEW.id)
        BEGIN
            SELECT RAISE(ABORT, 'historial inmutable');
        END
    """)
