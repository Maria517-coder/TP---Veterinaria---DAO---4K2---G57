"""Casos de uso del módulo Muestras y trazabilidad."""
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.cambio_estado import CambioEstado
from app.models.estado_remito import EstadoRemito
from app.models.muestra_biologica import MuestraBiologica
from app.repositories.muestra_repository import MuestraRepository
from app.repositories.remito_repository import RemitoRepository
from app.schemas.muestra import MuestraFiltros, ResultadoCrear


class MuestraService:
    """Orquesta los casos de uso de Muestras y trazabilidad."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = MuestraRepository(db)
        self.remitos = RemitoRepository(db)

    def listar(self, filtros: MuestraFiltros) -> list[MuestraBiologica]:
        """Devuelve las muestras que cumplen los filtros, ordenadas por id (E44)."""
        return self.repository.listar(**filtros.model_dump(exclude_none=True))

    def obtener_por_id(self, muestra_id: int) -> MuestraBiologica:
        """Devuelve una muestra existente o avisa que no existe (E45)."""
        muestra = self.repository.buscar_por_id(muestra_id)
        if muestra is None:
            raise RecursoNoEncontrado(f"No existe la muestra {muestra_id}")
        return muestra

    def historial_estados(self, muestra_id: int) -> list[CambioEstado]:
        """Devuelve el historial inmutable de cambios de estado (E46)."""
        return list(self.obtener_por_id(muestra_id).historial)

    def registrar_resultado(
        self, muestra_id: int, datos: ResultadoCrear
    ) -> MuestraBiologica:
        """Procesa una muestra Recibida y confirma el resultado (E47)."""
        muestra = self.obtener_por_id(muestra_id)
        if not muestra.puede_procesarse():
            raise ConflictoDeRecurso(
                f"No se puede registrar el resultado: la muestra {muestra_id} no está Recibida"
            )
        try:
            muestra.registrar_resultado(datos.texto, datos.responsable)
            self.repository.guardar(muestra)
            self._cerrar_remito_si_corresponde(muestra)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(muestra)
        return muestra

    def _cerrar_remito_si_corresponde(self, muestra: MuestraBiologica) -> None:
        """Cierra el remito en la misma transacción si ya no quedan muestras pendientes."""
        contenedor = muestra.contenedor
        if contenedor is None:
            return
        remito = self.remitos.buscar_por_contenedor(contenedor.id)
        if (
            remito is not None
            and remito.estado is EstadoRemito.RECIBIDO
            and contenedor.todas_muestras_finalizadas()
        ):
            remito.cerrar()
            self.remitos.guardar(remito)
