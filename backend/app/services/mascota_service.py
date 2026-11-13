"""Casos de uso del módulo Mascotas, historia clínica y vacunas."""
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado
from app.models.historia_clinica import HistoriaClinica
from app.models.consulta_medica import ConsultaMedica
from app.models.mascota import Mascota
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.mascota_repository import MascotaRepository
from app.schemas.mascota import MascotaActualizar, MascotaCrear
from app.models.aplicacion_vacuna import AplicacionVacuna
from app.models.vacuna import Vacuna
from app.repositories.vacuna_repository import VacunaRepository
from app.schemas.vacuna import VacunacionCrear


class MascotaService:
    """Orquesta los casos de uso de Mascotas, historia clínica y vacunas."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = MascotaRepository(db)
        self.clientes = ClienteRepository(db)

    def crear(self, datos: MascotaCrear) -> Mascota:
        """Da de alta la mascota y su historia clínica en una sola transacción."""
        self._validar_responsable(datos.cliente_id)
        self._validar_especie(datos.especie_id)

        mascota = Mascota(
            cliente_id=datos.cliente_id,
            especie_id=datos.especie_id,
            nombre=datos.nombre,
            fecha_nacimiento=datos.fecha_nacimiento,
        )
        try:
            # El flush asigna el id; el número de historia se deriva de él.
            self.repository.guardar(mascota)
            self.repository.guardar_historia(
                HistoriaClinica(mascota_id=mascota.id, numero=mascota.id)
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(mascota)
        return mascota

    def listar(
        self, cliente_id: int | None = None, especie_id: int | None = None
    ) -> list[Mascota]:
        """Devuelve las mascotas activas, opcionalmente filtradas."""
        return self.repository.listar(cliente_id, especie_id)

    def listar_por_cliente(self, cliente_id: int) -> list[Mascota]:
        """Devuelve las mascotas activas de un responsable que exista y esté activo."""
        self._validar_responsable(cliente_id)
        return self.repository.listar(cliente_id=cliente_id)

    def obtener(self, mascota_id: int) -> Mascota:
        """Devuelve una mascota activa o lanza RecursoNoEncontrado."""
        mascota = self.repository.buscar_por_id(mascota_id)
        if mascota is None:
            raise RecursoNoEncontrado(f"No existe la mascota {mascota_id}")
        return mascota

    def obtener_historia_clinica(self, mascota_id: int) -> HistoriaClinica:
        """Devuelve la historia clínica de una mascota activa."""
        return self.obtener(mascota_id).historia_clinica

    def obtener_historia_por_id(self, historia_id: int) -> HistoriaClinica:
        """Busca una historia clínica o informa que no existe."""
        historia = self.repository.buscar_historia(historia_id)
        if historia is None:
            raise RecursoNoEncontrado(f"No existe la historia clínica {historia_id}")
        return historia

    def listar_consultas(self, historia_id: int) -> list[ConsultaMedica]:
        """Devuelve las consultas asociadas a la historia."""
        return self.obtener_historia_por_id(historia_id).consultas

    def listar_vacunaciones(self, historia_id: int) -> list[AplicacionVacuna]:
        """Devuelve las aplicaciones registradas en la historia."""
        return self.obtener_historia_por_id(historia_id).aplicaciones

    def vacunas_pendientes(self, historia_id: int) -> list[Vacuna]:
        """Delega al dominio el cálculo de las vacunas pendientes."""
        return self.obtener_historia_por_id(historia_id).vacunas_pendientes()

    def registrar_vacunacion(
        self, historia_id: int, datos: VacunacionCrear
    ) -> AplicacionVacuna:
        """Delega el registro al modelo y confirma la aplicación."""
        historia = self.obtener_historia_por_id(historia_id)
        vacuna = VacunaRepository(self.db).buscar(datos.vacuna_id)
        if vacuna is None:
            raise RecursoNoEncontrado(f"No existe la vacuna {datos.vacuna_id}")
        try:
            historia.registrar_vacunacion(vacuna, datos.fecha)
            aplicacion = historia.aplicaciones[-1]
            self.repository.guardar_historia(historia)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(aplicacion)
        return aplicacion

    def actualizar(self, mascota_id: int, datos: MascotaActualizar) -> Mascota:
        """Reemplaza responsable, especie, nombre y fecha de nacimiento."""
        mascota = self.obtener(mascota_id)
        self._validar_responsable(datos.cliente_id)
        self._validar_especie(datos.especie_id)

        mascota.cliente_id = datos.cliente_id
        mascota.especie_id = datos.especie_id
        mascota.nombre = datos.nombre
        mascota.fecha_nacimiento = datos.fecha_nacimiento
        return self._persistir(mascota)

    def eliminar(self, mascota_id: int) -> None:
        """Da de baja lógica la mascota; conserva su historia y sus relaciones."""
        mascota = self.obtener(mascota_id)
        mascota.activo = False
        self._persistir(mascota)

    def _validar_responsable(self, cliente_id: int) -> None:
        """Exige que el cliente exista y esté activo."""
        if self.clientes.buscar_por_id(cliente_id) is None:
            raise RecursoNoEncontrado(f"No existe el cliente {cliente_id}")

    def _validar_especie(self, especie_id: int) -> None:
        """Exige que la especie exista."""
        if self.repository.buscar_especie(especie_id) is None:
            raise RecursoNoEncontrado(f"No existe la especie {especie_id}")

    def _persistir(self, mascota: Mascota) -> Mascota:
        """Guarda y confirma la transacción; ante cualquier error la deshace."""
        try:
            self.repository.guardar(mascota)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(mascota)
        return mascota
