"""Tests directos del TipoMuestraService, sin pasar por HTTP."""
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.tipo_muestra import TipoMuestra
from app.schemas.tipo_muestra import TipoMuestraActualizar, TipoMuestraCrear
from app.services.tipo_muestra_service import TipoMuestraService


def _datos(nombre: str = "SANGRE", costo: str = "1500.00") -> TipoMuestraCrear:
    """Arma un schema de alta con datos válidos."""
    return TipoMuestraCrear(nombre=nombre, costo_analisis=Decimal(costo))


def test_crear_guarda_y_confirma(db: Session) -> None:
    """crear persiste el tipo, hace commit y devuelve el modelo."""
    tipo = TipoMuestraService(db).crear(_datos("  SANGRE  "))
    tipo_id = tipo.id

    assert tipo_id is not None
    assert tipo.nombre == "SANGRE"
    assert tipo.costo_analisis == Decimal("1500.00")

    db.rollback()
    en_bd = db.get(TipoMuestra, tipo_id)
    assert en_bd is not None
    assert en_bd.nombre == "SANGRE"


def test_crear_rechaza_nombre_duplicado(db: Session) -> None:
    """No se pueden crear dos tipos con el mismo nombre exacto."""
    servicio = TipoMuestraService(db)
    servicio.crear(_datos("SANGRE"))

    with pytest.raises(ConflictoDeRecurso):
        servicio.crear(_datos("SANGRE", "999.00"))


def test_crear_compara_el_nombre_de_forma_exacta(db: Session) -> None:
    """Distinta mayúscula es distinto nombre: no se usa ilike."""
    servicio = TipoMuestraService(db)
    servicio.crear(_datos("SANGRE"))

    tipo = servicio.crear(_datos("sangre"))

    assert tipo.nombre == "sangre"


def test_crear_hace_rollback_si_falla_el_guardado(
    db: Session, monkeypatch
) -> None:
    """Si la persistencia falla, no queda un tipo a medias."""
    servicio = TipoMuestraService(db)

    def guardar_y_fallar(tipo: TipoMuestra) -> None:
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(servicio.repository, "guardar", guardar_y_fallar)

    with pytest.raises(RuntimeError):
        servicio.crear(_datos())

    assert db.query(TipoMuestra).count() == 0


def test_listar_devuelve_todos(db: Session) -> None:
    """listar delega en el repository."""
    servicio = TipoMuestraService(db)
    servicio.crear(_datos("SANGRE"))
    servicio.crear(_datos("ORINA"))

    nombres = [tipo.nombre for tipo in servicio.listar()]

    assert nombres == ["SANGRE", "ORINA"]


def test_obtener_devuelve_el_tipo(db: Session) -> None:
    """obtener devuelve el modelo cuando existe."""
    creado = TipoMuestraService(db).crear(_datos())

    assert TipoMuestraService(db).obtener(creado.id).id == creado.id


def test_obtener_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """Un id que no existe da 404 de dominio."""
    with pytest.raises(RecursoNoEncontrado):
        TipoMuestraService(db).obtener(9999)


def test_actualizar_reemplaza_y_confirma(db: Session) -> None:
    """actualizar cambia nombre y costo, hace commit y devuelve el modelo."""
    creado = TipoMuestraService(db).crear(_datos("SANGRE", "1500.00"))

    actualizado = TipoMuestraService(db).actualizar(
        creado.id,
        TipoMuestraActualizar(
            nombre="SANGRE TOTAL", costo_analisis=Decimal("1600.50")
        ),
    )
    tipo_id = actualizado.id

    assert actualizado.nombre == "SANGRE TOTAL"
    assert actualizado.costo_analisis == Decimal("1600.50")

    db.rollback()
    en_bd = db.get(TipoMuestra, tipo_id)
    assert en_bd is not None
    assert en_bd.nombre == "SANGRE TOTAL"


def test_actualizar_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """PUT sobre un id inexistente da 404."""
    with pytest.raises(RecursoNoEncontrado):
        TipoMuestraService(db).actualizar(
            9999,
            TipoMuestraActualizar(
                nombre="SANGRE", costo_analisis=Decimal("1500.00")
            ),
        )


def test_actualizar_rechaza_nombre_de_otro_tipo(db: Session) -> None:
    """PUT con el nombre de otro tipo da 409."""
    servicio = TipoMuestraService(db)
    sangre = servicio.crear(_datos("SANGRE"))
    servicio.crear(_datos("ORINA"))

    with pytest.raises(ConflictoDeRecurso):
        servicio.actualizar(
            sangre.id,
            TipoMuestraActualizar(
                nombre="ORINA", costo_analisis=Decimal("1500.00")
            ),
        )


def test_actualizar_puede_mantener_su_propio_nombre(db: Session) -> None:
    """El chequeo de duplicado excluye al registro que se está editando."""
    servicio = TipoMuestraService(db)
    creado = servicio.crear(_datos("SANGRE"))

    actualizado = servicio.actualizar(
        creado.id,
        TipoMuestraActualizar(
            nombre="SANGRE", costo_analisis=Decimal("1700.00")
        ),
    )

    assert actualizado.nombre == "SANGRE"
    assert actualizado.costo_analisis == Decimal("1700.00")
