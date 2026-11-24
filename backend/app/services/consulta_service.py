"""Casos de uso del módulo Consultas y derivación."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.consulta_medica import ConsultaMedica
from app.models.muestra_biologica import MuestraBiologica
from app.models.vacuna import Vacuna
from app.repositories.clinica_repository import ClinicaRepository
from app.repositories.consulta_repository import ConsultaRepository
from app.repositories.mascota_repository import MascotaRepository
from app.schemas.consulta import ConsultaCrear, MuestraCrear
from app.services.mascota_service import MascotaService


class ConsultaService:
    """Orquesta los casos de uso de Consultas y derivación."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ConsultaRepository(db)
        self.clinicas = ClinicaRepository(db)
        self.mascotas = MascotaRepository(db)

    def crear(self, datos: ConsultaCrear) -> tuple[ConsultaMedica, list[Vacuna]]:
        """E36: registra la atención y devuelve el aviso de vacunas pendientes."""
        veterinario = self.clinicas.buscar_veterinario_por_id(datos.veterinario_id)
        if veterinario is None:
            raise RecursoNoEncontrado(f"No existe el veterinario {datos.veterinario_id}")
        if self.clinicas.buscar_clinica_por_id(veterinario.clinica_id) is None:
            raise RecursoNoEncontrado(f"No existe la clínica {veterinario.clinica_id}")
        mascota = self.mascotas.buscar_por_id(datos.mascota_id)
        if mascota is None:
            raise RecursoNoEncontrado(f"No existe la mascota {datos.mascota_id}")

        # El esquema obligatorio ya está implementado en la historia clínica: solo se avisa.
        pendientes = MascotaService(self.db).vacunas_pendientes(
            mascota.historia_clinica.id
        )
        consulta = ConsultaMedica(
            numero=self.repository.siguiente_numero(),
            clinica_id=veterinario.clinica_id,
            veterinario_id=veterinario.id,
            mascota_id=mascota.id,
            fecha=datos.fecha,
            complejidad=datos.complejidad,
            costo=datos.costo,
        )
        try:
            self.repository.guardar(consulta)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(consulta)
        return consulta, pendientes

    def listar(
        self,
        clinica_id: int | None = None,
        fecha: date | None = None,
        mascota_id: int | None = None,
        veterinario_id: int | None = None,
        con_muestras: bool | None = None,
    ) -> list[ConsultaMedica]:
        """E37: devuelve las consultas con los filtros combinados."""
        return self.repository.listar(
            clinica_id, fecha, mascota_id, veterinario_id, con_muestras
        )

    def obtener(self, consulta_id: int) -> ConsultaMedica:
        """E38: devuelve una consulta existente o informa que no existe."""
        consulta = self.repository.buscar_por_id(consulta_id)
        if consulta is None:
            raise RecursoNoEncontrado(f"No existe la consulta {consulta_id}")
        return consulta

    def registrar_muestra(
        self, consulta_id: int, datos: MuestraCrear
    ) -> MuestraBiologica:
        """E39: crea la muestra en Extraida con el veterinario como responsable."""
        consulta = self.obtener(consulta_id)
        tipo = self.clinicas.buscar_tipo_muestra_por_id(datos.tipo_muestra_id)
        if tipo is None:
            raise RecursoNoEncontrado(
                f"No existe el tipo de muestra {datos.tipo_muestra_id}"
            )
        muestra = consulta.registrar_muestra(tipo, consulta.veterinario.nombre)
        try:
            self.repository.guardar_muestra(muestra)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(muestra)
        return muestra

    def listar_muestras(self, consulta_id: int) -> list[MuestraBiologica]:
        """E40: devuelve las muestras de una consulta existente."""
        return list(self.obtener(consulta_id).muestras)

    def orden_derivacion(self, consulta_id: int) -> bytes:
        """E41: genera el PDF de derivación; exige al menos una muestra."""
        consulta = self.obtener(consulta_id)
        if not consulta.tiene_muestras():
            raise ConflictoDeRecurso(
                f"La consulta {consulta_id} no tiene muestras para derivar"
            )
        return consulta.emitir_orden_derivacion()

    def comprobante(self, consulta_id: int) -> bytes:
        """E42: genera el PDF del comprobante, con resultados si los hay."""
        return self.obtener(consulta_id).imprimir_comprobante()

    def costo_total(self, consulta_id: int) -> Decimal:
        """E43: delega el cálculo en el dominio, sin reimplementarlo."""
        return self.obtener(consulta_id).costo_total()
