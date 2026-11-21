"""Casos de uso del módulo Agenda y turnos."""
from datetime import date

from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado, TurnoSuperpuesto
from app.models.turno import Turno
from app.models.veterinario import Veterinario
from app.repositories.clinica_repository import ClinicaRepository
from app.repositories.mascota_repository import MascotaRepository
from app.repositories.turno_repository import TurnoRepository
from app.schemas.turno import TurnoCrear, TurnoDisponibilidad


class TurnoService:
    """Orquesta los casos de uso de Agenda y turnos."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TurnoRepository(db)
        self.clinicas = ClinicaRepository(db)
        self.mascotas = MascotaRepository(db)

    def crear(self, veterinario_id: int, datos: TurnoCrear) -> Turno:
        """Reserva un turno: valida existencias y choque, y confirma todo junto."""
        veterinario = self.clinicas.buscar_veterinario_por_id(veterinario_id)
        if veterinario is None:
            raise RecursoNoEncontrado(f"No existe el veterinario {veterinario_id}")

        mascota = self.mascotas.buscar_por_id(datos.mascota_id)
        if mascota is None:
            raise RecursoNoEncontrado(f"No existe la mascota {datos.mascota_id}")

        # Candidato transitorio: valida contra los turnos ya persistidos sin
        # agregarse a la relación (así no se detecta a sí mismo como solape).
        candidato = Turno(inicio=datos.inicio, fin=datos.fin, activo=True)
        if veterinario.agenda.hay_superposicion(candidato):
            raise TurnoSuperpuesto("El turno se superpone con otro de la agenda")

        turno = Turno(
            veterinario=veterinario,
            mascota=mascota,
            inicio=datos.inicio,
            fin=datos.fin,
        )
        try:
            self.repository.guardar(turno)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(turno)
        return turno

    def listar_agenda(
        self, veterinario_id: int, fecha: date | None = None
    ) -> list[Turno]:
        """Devuelve los turnos vigentes del veterinario, ordenados por inicio."""
        self._validar_veterinario(veterinario_id)
        return self.repository.listar_por_veterinario(veterinario_id, fecha)

    def consultar_disponibilidad(
        self, veterinario_id: int, intervalo: TurnoDisponibilidad
    ) -> bool:
        """Indica si el intervalo está libre en la agenda del veterinario."""
        veterinario = self._validar_veterinario(veterinario_id)
        candidato = Turno(
            inicio=intervalo.inicio, fin=intervalo.fin, activo=True
        )
        return not veterinario.agenda.hay_superposicion(candidato)

    def cancelar(self, turno_id: int) -> None:
        """Da de baja lógica el turno, conservando la fila para trazabilidad."""
        turno = self.repository.buscar_por_id(turno_id)
        if turno is None:
            raise RecursoNoEncontrado(f"No existe el turno {turno_id}")
        try:
            turno.activo = False
            self.repository.guardar(turno)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _validar_veterinario(self, veterinario_id: int) -> Veterinario:
        """Exige un veterinario existente y activo; inactivo cuenta como inexistente."""
        veterinario = self.clinicas.buscar_veterinario_por_id(veterinario_id)
        if veterinario is None:
            raise RecursoNoEncontrado(f"No existe el veterinario {veterinario_id}")
        return veterinario
