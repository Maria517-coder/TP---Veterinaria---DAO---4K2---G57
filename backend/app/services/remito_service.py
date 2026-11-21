"""Casos de uso del módulo Remitos biológicos."""
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado
from app.models.remito_biologico import RemitoBiologico
from app.repositories.remito_repository import RemitoRepository
from app.schemas.remito import RemitoFiltros, ResponsableAccion


class RemitoService:
    """Orquesta los casos de uso de Remitos biológicos."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RemitoRepository(db)

    def listar(self, filtros: RemitoFiltros) -> list[RemitoBiologico]:
        """E55: devuelve remitos filtrados por estado, clínica y fechas."""
        return self.repository.listar(**filtros.model_dump(exclude_none=True))

    def obtener(self, remito_id: int) -> RemitoBiologico:
        """E56: devuelve un remito existente o informa que no existe."""
        remito = self.repository.buscar_por_id(remito_id)
        if remito is None:
            raise RecursoNoEncontrado(f"No existe el remito {remito_id}")
        return remito

    def imprimir(self, remito_id: int) -> bytes:
        """E57: devuelve el remito imprimible en PDF."""
        return self.obtener(remito_id).imprimir()

    def despachar(
        self, remito_id: int, datos: ResponsableAccion
    ) -> RemitoBiologico:
        """E58: despacha el remito y manda sus muestras a EnTransito."""
        remito = self.obtener(remito_id)
        remito.despachar(datos.responsable)
        return self._persistir(remito)

    def recepcionar(
        self, remito_id: int, datos: ResponsableAccion
    ) -> RemitoBiologico:
        """E59: registra la recepción y devuelve el estado final del remito."""
        remito = self.obtener(remito_id)
        remito.registrar_recepcion(datos.responsable)
        return self._persistir(remito)

    def tiempo_transito(self, remito_id: int) -> float:
        """E60: devuelve en segundos la diferencia entre despacho y recepción."""
        return self.obtener(remito_id).tiempo_transito()

    def _persistir(self, remito: RemitoBiologico) -> RemitoBiologico:
        """Guarda y confirma la transacción; ante cualquier error la deshace."""
        try:
            self.repository.guardar(remito)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(remito)
        return remito
