"""Seeds: carga de catálogos iniciales e idempotencia."""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import ReglaDeNegocioViolada
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.red_veterinaria import RedVeterinaria
from app.models.tipo_muestra import TipoMuestra
from app.seeds.datos_iniciales import cargar_datos_iniciales

ESTADOS_ESPERADOS = {
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
}

ESPECIES_ESPERADAS = {"PERRO", "GATO", "OTRO"}

TIPOS_ESPERADOS = {
    "SANGRE": Decimal("1500.00"),
    "ORINA": Decimal("1200.00"),
    "HECES": Decimal("1000.00"),
    "HISOPADO": Decimal("1800.00"),
    "TEJIDO": Decimal("2500.00"),
}


def _contar(db: Session, modelo: type) -> int:
    """Cuenta las filas de una tabla."""
    return db.scalar(select(func.count()).select_from(modelo)) or 0


def test_seed_carga_los_catalogos(db: Session) -> None:
    """El seed deja los estados, las especies y los tipos de muestra esperados."""
    cargar_datos_iniciales(db)

    estados = set(db.scalars(select(EstadoCatalogo.nombre)))
    especies = set(db.scalars(select(Especie.nombre)))
    tipos = {
        tipo.nombre: tipo.costo_analisis
        for tipo in db.scalars(select(TipoMuestra))
    }

    assert estados == ESTADOS_ESPERADOS
    assert especies == ESPECIES_ESPERADAS
    assert tipos == TIPOS_ESPERADOS
    assert all(isinstance(costo, Decimal) for costo in tipos.values())
    assert all(costo.as_tuple().exponent == -2 for costo in tipos.values())


def test_seed_es_idempotente(db: Session) -> None:
    """Correr el seed dos veces no duplica filas."""
    cargar_datos_iniciales(db)
    cargar_datos_iniciales(db)

    assert _contar(db, EstadoCatalogo) == len(ESTADOS_ESPERADOS)
    assert _contar(db, Especie) == len(ESPECIES_ESPERADAS)
    assert _contar(db, TipoMuestra) == len(TIPOS_ESPERADOS)


def test_seed_respeta_rollback_del_llamador(db: Session) -> None:
    """La carga no confirma ni siquiera los cambios previos del llamador."""
    db.add(Especie(nombre="PRUEBA"))
    cargar_datos_iniciales(db)
    db.rollback()

    assert _contar(db, EstadoCatalogo) == 0
    assert _contar(db, Especie) == 0
    assert _contar(db, TipoMuestra) == 0
    assert _contar(db, RedVeterinaria) == 0


def test_seed_crea_la_red_unica(db: Session) -> None:
    """Una base vacía recibe la red inicial sin confirmarla."""
    cargar_datos_iniciales(db)

    red = db.scalars(select(RedVeterinaria)).one()
    assert red.nombre == "Red Veterinaria"
    assert red.clinicas == []


def test_seed_repetido_reutiliza_la_misma_red(db: Session) -> None:
    """Repetir la inicialización conserva la identidad de la red."""
    cargar_datos_iniciales(db)
    red_id = db.scalar(select(RedVeterinaria.id))
    cargar_datos_iniciales(db)

    assert red_id is not None
    assert list(db.scalars(select(RedVeterinaria.id))) == [red_id]


def test_seed_respeta_commit_externo_y_nueva_sesion(db: Session) -> None:
    """El llamador confirma y otra sesión reutiliza la red guardada."""
    cargar_datos_iniciales(db)
    red_id = db.scalar(select(RedVeterinaria.id))
    db.commit()

    with Session(db.get_bind()) as otra:
        cargar_datos_iniciales(otra)
        assert red_id is not None
        assert list(otra.scalars(select(RedVeterinaria.id))) == [red_id]
        otra.rollback()

    assert db.scalar(select(RedVeterinaria.id)) == red_id


def test_seed_no_confirma_cambios_en_red_y_clinicas(db: Session) -> None:
    """El rollback externo conserva los datos anteriores a la carga."""
    red = RedVeterinaria(id=7, nombre="Red original")
    clinica = ClinicaVeterinaria(nombre="Clínica original", red=red)
    db.add(clinica)
    db.commit()
    red.nombre = "Cambio sin confirmar"
    clinica.nombre = "Otro cambio sin confirmar"

    cargar_datos_iniciales(db)
    db.rollback()

    assert red.nombre == "Red original"
    assert clinica.nombre == "Clínica original"
    assert _contar(db, EstadoCatalogo) == 0


def test_seed_reutiliza_red_pendiente(db: Session) -> None:
    """Una red pendiente del llamador no causa una segunda inserción."""
    red = RedVeterinaria(nombre="Red pendiente")
    db.add(red)

    cargar_datos_iniciales(db)

    assert list(db.scalars(select(RedVeterinaria))) == [red]
    assert red.nombre == "Red pendiente"


def test_arranque_crea_la_red(client: TestClient, db: Session) -> None:
    """El lifespan inicializa la red sin un alta manual."""
    assert client.get("/api/health").status_code == 200
    assert list(db.scalars(select(RedVeterinaria.nombre))) == ["Red Veterinaria"]


def test_seed_actualiza_base_anterior_sin_perder_datos(db: Session) -> None:
    """Una base sin índice conserva su red y clínicas y rechaza otra red."""
    db.execute(text("DROP INDEX IF EXISTS uq_red_veterinaria_unica"))
    red = RedVeterinaria(id=7, nombre="Nombre existente")
    clinica = ClinicaVeterinaria(nombre="Clínica existente", red=red)
    db.add(clinica)
    db.commit()
    clinica_id = clinica.id

    cargar_datos_iniciales(db)
    db.commit()

    assert red.id == 7
    assert red.nombre == "Nombre existente"
    assert [(c.id, c.nombre, c.red_id) for c in red.clinicas] == [
        (clinica_id, "Clínica existente", 7)
    ]
    db.add(RedVeterinaria(nombre="Otra red"))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert _contar(db, RedVeterinaria) == 1


def test_seed_rechaza_varias_redes_sin_modificar_datos(db: Session) -> None:
    """Los datos anteriores inconsistentes se informan y quedan intactos."""
    db.execute(text("DROP INDEX IF EXISTS uq_red_veterinaria_unica"))
    db.add_all([
        ClinicaVeterinaria(nombre="Centro", red=RedVeterinaria(nombre="Primera")),
        ClinicaVeterinaria(nombre="Sur", red=RedVeterinaria(nombre="Segunda")),
    ])
    db.commit()
    redes_antes = list(db.execute(select(RedVeterinaria.id, RedVeterinaria.nombre)))
    clinicas_antes = list(db.execute(select(
        ClinicaVeterinaria.id, ClinicaVeterinaria.nombre, ClinicaVeterinaria.red_id
    )))

    with pytest.raises(ReglaDeNegocioViolada, match="varias redes"):
        cargar_datos_iniciales(db)

    assert list(db.execute(select(RedVeterinaria.id, RedVeterinaria.nombre))) == redes_antes
    assert list(db.execute(select(
        ClinicaVeterinaria.id, ClinicaVeterinaria.nombre, ClinicaVeterinaria.red_id
    ))) == clinicas_antes
    assert _contar(db, EstadoCatalogo) == 0
    assert _contar(db, Especie) == 0
    assert _contar(db, TipoMuestra) == 0


def test_seed_rechaza_varias_redes_pendientes_sin_flush(db: Session) -> None:
    """La validación tampoco inserta redes pendientes inconsistentes."""
    db.add_all([RedVeterinaria(nombre="Una"), RedVeterinaria(nombre="Otra")])

    with pytest.raises(ReglaDeNegocioViolada, match="varias redes"):
        cargar_datos_iniciales(db)

    assert _contar(db, RedVeterinaria) == 0
    assert _contar(db, EstadoCatalogo) == 0
