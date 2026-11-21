"""Tests directos del VeterinarioService, sin pasar por HTTP."""
import pytest
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria
from app.models.veterinario import Veterinario
from app.schemas.veterinario import VeterinarioActualizar, VeterinarioCrear
from app.services.veterinario_service import VeterinarioService


@pytest.fixture()
def clinica(db: Session) -> ClinicaVeterinaria:
    """Persiste una clínica dentro de la red para los casos de uso."""
    red = RedVeterinaria(nombre="Red")
    db.add(red)
    db.flush()
    objeto = ClinicaVeterinaria(nombre="Centro", red=red)
    db.add(objeto)
    db.commit()
    return objeto


def _datos(
    matricula: str = "MP-123", nombre: str = "Eva"
) -> VeterinarioCrear:
    """Arma un schema de alta con datos válidos."""
    return VeterinarioCrear(matricula=matricula, nombre=nombre)


def test_crear_en_clinica(db: Session, clinica: ClinicaVeterinaria) -> None:
    """E25: alta con recorte, activo y vínculo con la clínica."""
    creado = VeterinarioService(db).crear_en_clinica(
        clinica.id, _datos("  MP-123  ", "  Eva  ")
    )
    veterinario_id = creado.id

    assert creado.matricula == "MP-123"
    assert creado.nombre == "Eva"
    assert creado.activo is True
    assert creado.clinica_id == clinica.id

    db.rollback()
    en_bd = db.get(Veterinario, veterinario_id)
    assert en_bd is not None
    assert en_bd.nombre == "Eva"


def test_crear_en_clinica_no_persiste_agenda(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    """La Agenda es solo la property sobre turnos: no hay campos nuevos."""
    creado = VeterinarioService(db).crear_en_clinica(clinica.id, _datos())

    assert creado.agenda.turnos == []


def test_crear_en_clinica_inexistente_da_404(db: Session) -> None:
    with pytest.raises(RecursoNoEncontrado):
        VeterinarioService(db).crear_en_clinica(9999, _datos())


def test_crear_rechaza_matricula_duplicada(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    servicio = VeterinarioService(db)
    servicio.crear_en_clinica(clinica.id, _datos("MP-123", "Eva"))

    with pytest.raises(ConflictoDeRecurso):
        servicio.crear_en_clinica(clinica.id, _datos("MP-123", "Ana"))


def test_matricula_de_inactivo_tambien_bloquea(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    """La columna unique no se libera con la baja lógica."""
    servicio = VeterinarioService(db)
    creado = servicio.crear_en_clinica(clinica.id, _datos("MP-123", "Eva"))
    servicio.eliminar(creado.id)

    with pytest.raises(ConflictoDeRecurso):
        servicio.crear_en_clinica(clinica.id, _datos("MP-123", "Ana"))


def test_crear_compara_matricula_de_forma_exacta(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    servicio = VeterinarioService(db)
    servicio.crear_en_clinica(clinica.id, _datos("MP-123", "Eva"))

    creado = servicio.crear_en_clinica(clinica.id, _datos("mp-123", "Ana"))

    assert creado.matricula == "mp-123"


def test_crear_hace_rollback_si_falla_el_guardado(
    db: Session, clinica: ClinicaVeterinaria, monkeypatch
) -> None:
    servicio = VeterinarioService(db)

    def guardar_y_fallar(entidad: object) -> None:
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(servicio.repository, "guardar", guardar_y_fallar)

    with pytest.raises(RuntimeError):
        servicio.crear_en_clinica(clinica.id, _datos())

    assert db.query(Veterinario).count() == 0


def test_listar_por_clinica(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    """E26: lista solo los activos de esa clínica."""
    servicio = VeterinarioService(db)
    eva = servicio.crear_en_clinica(clinica.id, _datos("MP-1", "Eva"))
    servicio.crear_en_clinica(clinica.id, _datos("MP-2", "Ana"))
    servicio.eliminar(eva.id)

    assert [vet.nombre for vet in servicio.listar_por_clinica(clinica.id)] == ["Ana"]


def test_listar_por_clinica_inexistente_da_404(db: Session) -> None:
    with pytest.raises(RecursoNoEncontrado):
        VeterinarioService(db).listar_por_clinica(9999)


def test_actualizar(db: Session, clinica: ClinicaVeterinaria) -> None:
    """E27: reemplaza nombre y matrícula, y confirma."""
    servicio = VeterinarioService(db)
    creado = servicio.crear_en_clinica(clinica.id, _datos("MP-1", "Eva"))

    actualizado = servicio.actualizar(
        creado.id,
        VeterinarioActualizar(matricula="MP-9", nombre="Eva María"),
    )
    veterinario_id = actualizado.id

    assert actualizado.matricula == "MP-9"
    assert actualizado.nombre == "Eva María"
    db.rollback()
    assert db.get(Veterinario, veterinario_id).nombre == "Eva María"


def test_actualizar_puede_mantener_su_matricula(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    """El chequeo de duplicado excluye al propio veterinario."""
    servicio = VeterinarioService(db)
    creado = servicio.crear_en_clinica(clinica.id, _datos("MP-1", "Eva"))

    actualizado = servicio.actualizar(
        creado.id, VeterinarioActualizar(matricula="MP-1", nombre="Eva María")
    )

    assert actualizado.matricula == "MP-1"


def test_actualizar_rechaza_matricula_de_otro(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    servicio = VeterinarioService(db)
    eva = servicio.crear_en_clinica(clinica.id, _datos("MP-1", "Eva"))
    servicio.crear_en_clinica(clinica.id, _datos("MP-2", "Ana"))

    with pytest.raises(ConflictoDeRecurso):
        servicio.actualizar(
            eva.id, VeterinarioActualizar(matricula="MP-2", nombre="Eva")
        )


def test_actualizar_inexistente_da_404(db: Session) -> None:
    with pytest.raises(RecursoNoEncontrado):
        VeterinarioService(db).actualizar(
            9999, VeterinarioActualizar(matricula="MP-1", nombre="Eva")
        )


def test_eliminar_es_baja_logica(
    db: Session, clinica: ClinicaVeterinaria
) -> None:
    """E28: 204 implícito en el service; la fila queda como inactiva."""
    servicio = VeterinarioService(db)
    creado = servicio.crear_en_clinica(clinica.id, _datos())

    servicio.eliminar(creado.id)

    assert db.get(Veterinario, creado.id).activo is False
    with pytest.raises(RecursoNoEncontrado):
        servicio.actualizar(
            creado.id, VeterinarioActualizar(matricula="MP-123", nombre="Eva")
        )


def test_eliminar_inexistente_da_404(db: Session) -> None:
    with pytest.raises(RecursoNoEncontrado):
        VeterinarioService(db).eliminar(9999)
