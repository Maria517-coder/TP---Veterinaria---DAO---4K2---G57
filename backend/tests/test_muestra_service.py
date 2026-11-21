"""Casos de uso de consulta y trazabilidad de muestras (E44 a E46)."""
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models import (
    CambioEstado,
    Cliente,
    ClinicaVeterinaria,
    Complejidad,
    ConsultaMedica,
    Especie,
    EstadoCatalogo,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    TipoMuestra,
    Veterinario,
)
from app.models.estados import Analizada, Empaquetada, EnTransito, Recibida
from app.schemas.muestra import MuestraFiltros, ResultadoCrear
from app.services.muestra_service import MuestraService

NOMBRES_ESTADOS = (
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
)


@pytest.fixture()
def muestra(db: Session) -> MuestraBiologica:
    """Persiste una muestra Extraida con su contexto mínimo y el catálogo completo."""
    clinica = ClinicaVeterinaria(nombre="Centro", red=RedVeterinaria(nombre="Red"))
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=date(2020, 1, 1),
        responsable=Cliente(nombre="Ana", telefono="123"),
        especie=Especie(nombre="PERRO"),
        historia_clinica=HistoriaClinica(numero=1),
    )
    consulta = ConsultaMedica(
        numero=1,
        clinica=clinica,
        mascota=mascota,
        veterinario=Veterinario(nombre="Eva", matricula="123", clinica=clinica),
        fecha=datetime.now().date(),
        complejidad=Complejidad.BAJA,
        costo=Decimal("100.00"),
    )
    estados = {nombre: EstadoCatalogo(nombre=nombre) for nombre in NOMBRES_ESTADOS}
    db.add_all(list(estados.values()))
    objeto = MuestraBiologica(
        consulta=consulta,
        tipo=TipoMuestra(nombre="SANGRE", costo_analisis=Decimal("1500.00")),
        estado_actual=estados["Extraida"],
        fecha=datetime.now().date(),
    )
    db.add(objeto)
    db.commit()
    return objeto


def test_listar_aplica_los_filtros_del_schema(db: Session, muestra: MuestraBiologica) -> None:
    """El service pasa los filtros al repositorio y devuelve las muestras."""
    servicio = MuestraService(db)

    assert servicio.listar(MuestraFiltros(estado="Extraida")) == [muestra]
    assert servicio.listar(
        MuestraFiltros(clinica_id=muestra.consulta.clinica_id, fecha=muestra.fecha)
    ) == [muestra]


def test_listar_con_estado_valido_sin_muestras_devuelve_lista_vacia(
    db: Session, muestra: MuestraBiologica
) -> None:
    """Un estado permitido pero sin muestras no es error: es una lista vacía."""
    assert MuestraService(db).listar(MuestraFiltros(estado="Analizada")) == []


def test_obtener_por_id_devuelve_la_muestra(db: Session, muestra: MuestraBiologica) -> None:
    """La consulta por id devuelve la entidad del dominio."""
    assert MuestraService(db).obtener_por_id(muestra.id) is muestra


def test_obtener_por_id_inexistente_lanza_recurso_no_encontrado(
    db: Session, muestra: MuestraBiologica
) -> None:
    """No existe equivale a 404; el mensaje nombra el id pedido."""
    with pytest.raises(RecursoNoEncontrado, match=str(muestra.id + 999)):
        MuestraService(db).obtener_por_id(muestra.id + 999)


def test_historial_estados_devuelve_los_cambios_en_orden(
    db: Session, muestra: MuestraBiologica
) -> None:
    """La trazabilidad se lee del historial inmutable, sin editarlo."""
    muestra.cambiar_estado(Empaquetada(), "Eva")
    muestra.cambiar_estado(EnTransito(), "Eva")
    db.flush()

    registros = MuestraService(db).historial_estados(muestra.id)

    assert all(isinstance(registro, CambioEstado) for registro in registros)
    assert [registro.estado.nombre for registro in registros] == [
        "Empaquetada",
        "EnTransito",
    ]
    assert all(registro.muestra_id == muestra.id for registro in registros)


def test_historial_estados_de_muestra_inexistente_lanza_404(
    db: Session, muestra: MuestraBiologica
) -> None:
    """Pedir el historial de una muestra inexistente también da 404."""
    with pytest.raises(RecursoNoEncontrado, match="muestra"):
        MuestraService(db).historial_estados(muestra.id + 999)


def _llevar_a_recibida(muestra: MuestraBiologica) -> None:
    """Recorre el ciclo válido hasta Recibida para poder procesar la muestra."""
    muestra.cambiar_estado(Empaquetada(), "Eva")
    muestra.cambiar_estado(EnTransito(), "Eva")
    muestra.cambiar_estado(Recibida(), "Eva")


def test_registrar_resultado_confirma_el_resultado_y_el_cambio_a_analizada(
    db: Session, muestra: MuestraBiologica
) -> None:
    """E47 guarda el texto, la fecha de hoy y deja el cambio de estado persistido."""
    _llevar_a_recibida(muestra)
    db.flush()
    servicio = MuestraService(db)

    actualizada = servicio.registrar_resultado(
        muestra.id,
        ResultadoCrear(texto="  Negativo  ", responsable=" Luis "),
    )

    assert actualizada.resultado == "Negativo"
    assert actualizada.fecha_resultado == datetime.now().date()
    assert isinstance(actualizada.estado, Analizada)
    assert actualizada.historial[-1].responsable == "Luis"
    assert actualizada.historial[-1].estado.nombre == "Analizada"

    db.refresh(actualizada)
    assert actualizada.resultado == "Negativo"
    assert isinstance(actualizada.estado, Analizada)


def test_registrar_resultado_conflicto_no_muta_la_muestra(
    db: Session, muestra: MuestraBiologica
) -> None:
    """Si no está Recibida, se avisa antes de tocar resultado, fecha o historial."""
    servicio = MuestraService(db)

    with pytest.raises(ConflictoDeRecurso, match="Recibida"):
        servicio.registrar_resultado(
            muestra.id, ResultadoCrear(texto="Negativo", responsable="Luis")
        )

    db.refresh(muestra)
    assert muestra.resultado is None
    assert muestra.fecha_resultado is None
    assert muestra.estado.nombre == "Extraida"
    assert muestra.historial == []


def test_registrar_resultado_de_muestra_inexistente_lanza_404(
    db: Session, muestra: MuestraBiologica
) -> None:
    """Primero se comprueba la existencia; después recién se evaluá el estado."""
    with pytest.raises(RecursoNoEncontrado, match="muestra"):
        MuestraService(db).registrar_resultado(
            muestra.id + 999,
            ResultadoCrear(texto="Negativo", responsable="Luis"),
        )
