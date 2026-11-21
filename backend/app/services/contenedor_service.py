"""Casos de uso del módulo Contenedores de envío."""
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado
from app.models.contenedor_envio import ContenedorEnvio
from app.models.remito_biologico import RemitoBiologico
from app.repositories.contenedor_repository import ContenedorRepository
from app.repositories.muestra_repository import MuestraRepository
from app.repositories.remito_repository import RemitoRepository
from app.schemas.contenedor import (
    ContenedorCrear,
    ContenedorFiltros,
    MuestraAgregar,
    RemitoGenerar,
)


class ContenedorService:
    """Orquesta los casos de uso de Contenedores de envío."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ContenedorRepository(db)
        self.muestras = MuestraRepository(db)
        self.remitos = RemitoRepository(db)

    def crear(self, datos: ContenedorCrear) -> ContenedorEnvio:
        """E48: da de alta un contenedor con precinto intacto y número correlativo."""
        contenedor = ContenedorEnvio(
            numero=self.repository.siguiente_numero(),
            precinto_intacto=True,
        )
        try:
            self.repository.guardar(contenedor)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(contenedor)
        return contenedor

    def listar(self, filtros: ContenedorFiltros) -> list[ContenedorEnvio]:
        """E49: devuelve contenedores filtrados por remito y rango de fechas."""
        return self.repository.listar(**filtros.model_dump(exclude_none=True))

    def obtener(self, contenedor_id: int) -> ContenedorEnvio:
        """E50: devuelve un contenedor existente o informa que no existe."""
        contenedor = self.repository.buscar_por_id(contenedor_id)
        if contenedor is None:
            raise RecursoNoEncontrado(f"No existe el contenedor {contenedor_id}")
        return contenedor

    def agregar_muestra(
        self, contenedor_id: int, datos: MuestraAgregar
    ) -> ContenedorEnvio:
        """E51: agrega una muestra Extraida de la misma clínica y la pasa a Empaquetada."""
        contenedor = self.obtener(contenedor_id)
        muestra = self.muestras.buscar_por_id(datos.muestra_id)
        if muestra is None:
            raise RecursoNoEncontrado(f"No existe la muestra {datos.muestra_id}")
        contenedor.agregar_muestra(muestra, datos.responsable)
        try:
            self.muestras.guardar(muestra)
            self.repository.guardar(contenedor)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(contenedor)
        return contenedor

    def romper_precinto(self, contenedor_id: int) -> ContenedorEnvio:
        """E52: deja el precinto roto sin vuelta atrás, salvo después de la recepción."""
        contenedor = self.obtener(contenedor_id)
        contenedor.romper_precinto()
        try:
            self.repository.guardar(contenedor)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(contenedor)
        return contenedor

    def generar_remito(
        self, contenedor_id: int, datos: RemitoGenerar
    ) -> RemitoBiologico:
        """E53: crea el remito GENERADO con el número correlativo que sigue."""
        contenedor = self.obtener(contenedor_id)
        remito = contenedor.generar_remito(
            datos.laboratorio_destino, self.remitos.siguiente_numero()
        )
        try:
            self.remitos.guardar(remito)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(remito)
        return remito

    def obtener_remito(self, contenedor_id: int) -> RemitoBiologico:
        """E54: devuelve el remito del contenedor o informa que aún no lo tiene."""
        contenedor = self.obtener(contenedor_id)
        remito = self.remitos.buscar_por_contenedor(contenedor.id)
        if remito is None:
            raise RecursoNoEncontrado(
                f"El contenedor {contenedor_id} todavía no tiene remito"
            )
        return remito
