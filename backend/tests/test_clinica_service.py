"""Tests directos del ClinicaService, sin pasar por HTTP."""
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria
from app.schemas.clinica import ClinicaVeterinariaActualizar, ClinicaVeterinariaCrear
from app.services.clinica_service import ClinicaService


@pytest.fixture()
def red(db: Session) -> RedVeterinaria:
    """Persiste la red única que necesitan los casos de uso."""
    objeto = RedVeterinaria(nombre="Red")
    db.add(objeto)
    db.commit()
    return objeto


def _datos(nombre: str = "Centro") -> ClinicaVeterinariaCrear:
    """Arma un schema de alta con un nombre válido."""
    return ClinicaVeterinariaCrear(nombre=nombre)


def test_obtener_red_devuelve_la_unica(db: Session, red: RedVeterinaria) -> None:
    """E20: la red sembrada se devuelve tal cual."""
    assert ClinicaService(db).obtener_red().id == red.id


def test_obtener_red_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """Sin red sembrada, avisamos en vez de devolver None."""
    with pytest.raises(RecursoNoEncontrado):
        ClinicaService(db).obtener_red()


def test_agregar_clinica_a_red(db: Session, red: RedVeterinaria) -> None:
    """E21: alta, recorte del nombre, vínculo con la red y commit."""
    creada = ClinicaService(db).agregar_clinica_a_red(_datos("  Centro  "))
    clinica_id = creada.id

    assert creada.nombre == "Centro"
    assert creada.red_id == red.id
    assert creada.red is red

    db.rollback()
    en_bd = db.get(ClinicaVeterinaria, clinica_id)
    assert en_bd is not None
    assert en_bd.nombre == "Centro"


def test_agregar_clinica_rechaza_nombre_duplicado(
    db: Session, red: RedVeterinaria
) -> None:
    """Dos clínicas no pueden tener el mismo nombre exacto."""
    servicio = ClinicaService(db)
    servicio.agregar_clinica_a_red(_datos("Centro"))

    with pytest.raises(ConflictoDeRecurso):
        servicio.agregar_clinica_a_red(_datos("Centro"))


def test_agregar_clinica_compara_de_forma_exacta(
    db: Session, red: RedVeterinaria
) -> None:
    """Distintamayúscula es distinto nombre: no se usa ilike."""
    servicio = ClinicaService(db)
    servicio.agregar_clinica_a_red(_datos("Centro"))

    creada = servicio.agregar_clinica_a_red(_datos("centro"))

    assert creada.nombre == "centro"


def test_agregar_clinica_hace_rollback_si_falla_el_guardado(
    db: Session, red: RedVeterinaria, monkeypatch
) -> None:
    """Si la persistencia falla, no queda una clínica a medias."""
    servicio = ClinicaService(db)

    def guardar_y_fallar(entidad: object) -> None:
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(servicio.repository, "guardar", guardar_y_fallar)

    with pytest.raises(RuntimeError):
        servicio.agregar_clinica_a_red(_datos())

    assert db.scalar(select(ClinicaVeterinaria.id).limit(1)) is None


def test_listar_clinicas(db: Session, red: RedVeterinaria) -> None:
    """E22: devuelve todas las clínicas de la red."""
    servicio = ClinicaService(db)
    servicio.agregar_clinica_a_red(_datos("Centro"))
    servicio.agregar_clinica_a_red(_datos("Sur"))

    assert [clinica.nombre for clinica in servicio.listar_clinicas()] == [
        "Centro",
        "Sur",
    ]


def test_obtener_clinica(db: Session, red: RedVeterinaria) -> None:
    """E23: devuelve la clínica por id."""
    creada = ClinicaService(db).agregar_clinica_a_red(_datos())

    assert ClinicaService(db).obtener_clinica(creada.id).nombre == "Centro"


def test_obtener_clinica_inexistente_lanza_recurso_no_encontrado(
    db: Session, red: RedVeterinaria
) -> None:
    """Un id que no existe da 404 de dominio."""
    with pytest.raises(RecursoNoEncontrado):
        ClinicaService(db).obtener_clinica(9999)


def test_actualizar_clinica(db: Session, red: RedVeterinaria) -> None:
    """E24: reemplaza el nombre y confirma."""
    creada = ClinicaService(db).agregar_clinica_a_red(_datos())

    actualizada = ClinicaService(db).actualizar_clinica(
        creada.id, ClinicaVeterinariaActualizar(nombre="Centro Norte")
    )
    clinica_id = actualizada.id

    assert actualizada.nombre == "Centro Norte"
    db.rollback()
    assert db.get(ClinicaVeterinaria, clinica_id).nombre == "Centro Norte"


def test_actualizar_clinica_inexistente_lanza_recurso_no_encontrado(
    db: Session, red: RedVeterinaria
) -> None:
    with pytest.raises(RecursoNoEncontrado):
        ClinicaService(db).actualizar_clinica(
            9999, ClinicaVeterinariaActualizar(nombre="Centro")
        )


def test_actualizar_clinica_rechaza_nombre_de_otra(
    db: Session, red: RedVeterinaria
) -> None:
    servicio = ClinicaService(db)
    centro = servicio.agregar_clinica_a_red(_datos("Centro"))
    servicio.agregar_clinica_a_red(_datos("Sur"))

    with pytest.raises(ConflictoDeRecurso):
        servicio.actualizar_clinica(
            centro.id, ClinicaVeterinariaActualizar(nombre="Sur")
        )


def test_actualizar_clinica_puede_mantener_su_propio_nombre(
    db: Session, red: RedVeterinaria
) -> None:
    """El chequeo de duplicado excluye a la clínica que se está editando."""
    servicio = ClinicaService(db)
    creada = servicio.agregar_clinica_a_red(_datos("Centro"))

    actualizada = servicio.actualizar_clinica(
        creada.id, ClinicaVeterinariaActualizar(nombre="Centro")
    )

    assert actualizada.nombre == "Centro"
