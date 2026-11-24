"""Tests del script de datos de demostración."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.estado_remito import EstadoRemito
from app.models.muestra_biologica import MuestraBiologica
from app.models.remito_biologico import RemitoBiologico
from app.models.usuario import RolUsuario, Usuario
from app.models.veterinario import Veterinario
from app.seeds.datos_demo import cargar_datos_demo
from app.seeds.datos_iniciales import cargar_datos_iniciales
from app.services.usuario_service import UsuarioService


def _preparar_base(db: Session) -> None:
    cargar_datos_iniciales(db)
    db.commit()
    UsuarioService(db).asegurar_admin_inicial("admin123")


def test_demo_crea_datos_principales(db: Session) -> None:
    """Una corrida deja clínicas, vets, usuario vet1/vet12345 y muestras en 6 estados."""
    _preparar_base(db)

    cargar_datos_demo(db)

    assert db.scalar(select(func.count()).select_from(ClinicaVeterinaria)) == 2
    assert (
        db.scalar(
            select(func.count())
            .select_from(Veterinario)
            .where(Veterinario.activo.is_(True))
        )
        == 3
    )

    from app.schemas.auth import LoginRequest

    respuesta = UsuarioService(db).login(
        LoginRequest(usuario="vet1", contrasena="vet12345")
    )
    assert respuesta["token"]
    assert respuesta["rol"] == RolUsuario.VETERINARIO.value
    assert respuesta["veterinario_id"] is not None

    muestras = list(db.scalars(select(MuestraBiologica)))
    nombres_estados = {m.estado.nombre for m in muestras}
    assert nombres_estados == {
        "Extraida",
        "Empaquetada",
        "EnTransito",
        "Recibida",
        "Analizada",
        "Rechazada",
    }


def test_demo_es_idempotente(db: Session) -> None:
    """Correrlo dos veces no duplica nada."""
    _preparar_base(db)

    cargar_datos_demo(db)
    conteos = {
        "clinicas": db.scalar(select(func.count()).select_from(ClinicaVeterinaria)),
        "vets": db.scalar(select(func.count()).select_from(Veterinario)),
        "usuarios": db.scalar(select(func.count()).select_from(Usuario)),
        "muestras": db.scalar(select(func.count()).select_from(MuestraBiologica)),
        "remitos": db.scalar(select(func.count()).select_from(RemitoBiologico)),
    }

    cargar_datos_demo(db)

    assert conteos == {
        "clinicas": db.scalar(select(func.count()).select_from(ClinicaVeterinaria)),
        "vets": db.scalar(select(func.count()).select_from(Veterinario)),
        "usuarios": db.scalar(select(func.count()).select_from(Usuario)),
        "muestras": db.scalar(select(func.count()).select_from(MuestraBiologica)),
        "remitos": db.scalar(select(func.count()).select_from(RemitoBiologico)),
    }


def test_demo_remito_analizada_queda_cerrado(db: Session) -> None:
    """El remito de la muestra Analizada queda CERRADO."""
    _preparar_base(db)
    cargar_datos_demo(db)

    analizadas = [
        m for m in db.scalars(select(MuestraBiologica)) if m.estado.nombre == "Analizada"
    ]
    assert analizadas
    for muestra in analizadas:
        assert muestra.contenedor is not None
        assert muestra.contenedor.remito is not None
        assert muestra.contenedor.remito.estado == EstadoRemito.CERRADO


def test_app_no_carga_datos_demo(client, db: Session) -> None:
    """Importar/iniciar la app NO carga datos de demo."""
    existe = db.scalar(
        select(func.count())
        .select_from(ClinicaVeterinaria)
        .where(ClinicaVeterinaria.nombre == "Clínica Central")
    )
    assert existe == 0
