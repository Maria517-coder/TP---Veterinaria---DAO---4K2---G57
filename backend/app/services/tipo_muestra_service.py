"""Casos de uso del módulo Tipos de muestra."""
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.tipo_muestra import TipoMuestra
from app.repositories.clinica_repository import ClinicaRepository
from app.schemas.tipo_muestra import TipoMuestraActualizar, TipoMuestraCrear


class TipoMuestraService:
    """Orquesta los casos de uso de Tipos de muestra."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ClinicaRepository(db)

    def crear(self, datos: TipoMuestraCrear) -> TipoMuestra:
        """Da de alta un tipo de muestra; el nombre no puede repetirse."""
        if self.repository.buscar_tipo_muestra_por_nombre(datos.nombre) is not None:
            raise ConflictoDeRecurso(f"Ya existe el tipo de muestra {datos.nombre}")
        tipo = TipoMuestra(nombre=datos.nombre, costo_analisis=datos.costo_analisis)
        return self._persistir(tipo)

    def listar(self) -> list[TipoMuestra]:
        """Devuelve todos los tipos de muestra."""
        return self.repository.listar_tipos_muestra()

    def obtener(self, tipo_id: int) -> TipoMuestra:
        """Devuelve un tipo o lanza RecursoNoEncontrado."""
        tipo = self.repository.buscar_tipo_muestra_por_id(tipo_id)
        if tipo is None:
            raise RecursoNoEncontrado(f"No existe el tipo de muestra {tipo_id}")
        return tipo

    def actualizar(self, tipo_id: int, datos: TipoMuestraActualizar) -> TipoMuestra:
        """Reemplaza nombre y costo, sin chocar con otro tipo."""
        tipo = self.obtener(tipo_id)
        duplicado = self.repository.buscar_tipo_muestra_por_nombre(datos.nombre)
        if duplicado is not None and duplicado.id != tipo.id:
            raise ConflictoDeRecurso(f"Ya existe el tipo de muestra {datos.nombre}")
        tipo.nombre = datos.nombre
        tipo.costo_analisis = datos.costo_analisis
        return self._persistir(tipo)

    def _persistir(self, tipo: TipoMuestra) -> TipoMuestra:
        """Guarda y confirma; ante cualquier error deshace la transacción."""
        try:
            self.repository.guardar(tipo)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(tipo)
        return tipo
