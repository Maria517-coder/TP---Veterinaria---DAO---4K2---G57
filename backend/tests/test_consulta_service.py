"""Casos de uso E36 a E38 del service de consultas."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.cliente import Cliente
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.complejidad import Complejidad
from app.models.consulta_medica import ConsultaMedica
from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.muestra_biologica import MuestraBiologica
from app.models.red_veterinaria import RedVeterinaria
from app.models.tipo_muestra import TipoMuestra
from app.models.vacuna import Vacuna
from app.models.veterinario import Veterinario
from app.repositories.consulta_repository import ConsultaRepository
from app.schemas.consulta import ConsultaCrear, MuestraCrear
from app.services.consulta_service import ConsultaService


@pytest.fixture()
def ctx(db: Session) -> dict:
    """Dos clínicas, dos veterinarios, dos mascotas y una vacuna obligatoria."""
    red = RedVeterinaria(nombre="Red S")
    db.add(red)
    db.flush()
    centro = ClinicaVeterinaria(nombre="Centro S", red=red)
    norte = ClinicaVeterinaria(nombre="Norte S", red=red)
    db.add_all([centro, norte])
    db.flush()
    eva = Veterinario(nombre="Eva", matricula="MP-S1", clinica=centro)
    luis = Veterinario(nombre="Luis", matricula="MP-S2", clinica=norte)
    especie = Especie(nombre="PERRO-S")
    rabia = Vacuna(nombre="Rabia-S", obligatoria=True, especies_aplicables=[especie])
    cliente = Cliente(nombre="Ana", telefono="123")
    db.add_all([eva, luis, rabia, cliente])
    db.flush()
    nacimiento = datetime.now().date() - timedelta(days=730)
    luna = Mascota(
        nombre="Luna", fecha_nacimiento=nacimiento, responsable=cliente,
        especie=especie, historia_clinica=HistoriaClinica(numero=901),
    )
    sol = Mascota(
        nombre="Sol", fecha_nacimiento=nacimiento, responsable=cliente,
        especie=especie, historia_clinica=HistoriaClinica(numero=902),
    )
    db.add_all([luna, sol])
    tipo = TipoMuestra(nombre="SANGRE-S", costo_analisis="1500.00")
    db.add_all([tipo, EstadoCatalogo(nombre="Extraida")])
    db.commit()
    return {
        "centro": centro.id, "norte": norte.id,
        "eva": eva.id, "luis": luis.id,
        "luna": luna.id, "sol": sol.id,
        "rabia": rabia.id, "tipo": tipo.id,
        "historia_luna": luna.historia_clinica.id,
        "historia_sol": sol.historia_clinica.id,
        "hoy": datetime.now().date(),
    }


def _datos(ctx: dict, **cambios) -> ConsultaCrear:
    base = {
        "veterinario_id": ctx["eva"],
        "mascota_id": ctx["luna"],
        "fecha": ctx["hoy"] - timedelta(days=1),
        "complejidad": Complejidad.BAJA,
        "costo": "100.00",
    }
    base.update(cambios)
    return ConsultaCrear(**base)


def test_crear_asigna_numero_y_clinica_del_veterinario(db: Session, ctx: dict) -> None:
    consulta, pendientes = ConsultaService(db).crear(_datos(ctx))

    assert consulta.numero == 1
    assert consulta.clinica_id == ctx["centro"]
    assert consulta.costo == Decimal("100.00")
    assert consulta.fecha == ctx["hoy"] - timedelta(days=1)
    assert [vacuna.id for vacuna in pendientes] == [ctx["rabia"]]
    assert [vacuna.nombre for vacuna in pendientes] == ["Rabia-S"]
    assert db.get(ConsultaMedica, consulta.id) is not None


def test_crear_siguiente_consulta_es_numero_dos(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)

    primera, _ = service.crear(_datos(ctx))
    segunda, _ = service.crear(_datos(ctx, fecha=ctx["hoy"] - timedelta(days=2)))

    assert (primera.numero, segunda.numero) == (1, 2)


def test_crear_avisa_esquema_incompleto(db: Session, ctx: dict) -> None:
    """La mascota sin la vacuna obligatoria no bloquea el alta: solo avisa."""
    _, pendientes = ConsultaService(db).crear(_datos(ctx))

    assert [(vacuna.id, vacuna.nombre) for vacuna in pendientes] == [
        (ctx["rabia"], "Rabia-S")
    ]


def test_crear_sin_pendientes_con_esquema_completo(db: Session, ctx: dict) -> None:
    historia = db.get(HistoriaClinica, ctx["historia_luna"])
    historia.registrar_vacunacion(
        db.get(Vacuna, ctx["rabia"]), ctx["hoy"] - timedelta(days=30)
    )
    db.commit()

    consulta, pendientes = ConsultaService(db).crear(_datos(ctx))

    assert consulta.numero == 1
    assert pendientes == []


def test_crear_veterinario_inexistente(db: Session, ctx: dict) -> None:
    with pytest.raises(RecursoNoEncontrado):
        ConsultaService(db).crear(_datos(ctx, veterinario_id=9999))

    assert ConsultaRepository(db).siguiente_numero() == 1


def test_crear_mascota_inexistente(db: Session, ctx: dict) -> None:
    with pytest.raises(RecursoNoEncontrado):
        ConsultaService(db).crear(_datos(ctx, mascota_id=9999))

    assert ConsultaRepository(db).siguiente_numero() == 1


def test_listar_con_filtros_combinables(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    ayer = ctx["hoy"] - timedelta(days=1)
    anteayer = ctx["hoy"] - timedelta(days=2)
    a, _ = service.crear(_datos(ctx, fecha=ayer))
    b, _ = service.crear(_datos(ctx, fecha=anteayer))
    c, _ = service.crear(
        _datos(ctx, fecha=ayer, veterinario_id=ctx["luis"], mascota_id=ctx["sol"])
    )
    a.registrar_muestra(db.get(TipoMuestra, ctx["tipo"]), "Dra. Eva")
    db.commit()

    ids = lambda lista: [consulta.id for consulta in lista]

    assert ids(service.listar()) == [a.id, b.id, c.id]
    assert ids(service.listar(clinica_id=ctx["norte"])) == [c.id]
    assert ids(service.listar(fecha=ayer)) == [a.id, c.id]
    assert ids(service.listar(mascota_id=ctx["luna"])) == [a.id, b.id]
    assert ids(service.listar(veterinario_id=ctx["eva"])) == [a.id, b.id]
    assert ids(service.listar(con_muestras=True)) == [a.id]
    assert ids(service.listar(clinica_id=ctx["centro"], fecha=ayer, con_muestras=True)) == [a.id]


def test_obtener_por_id(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    creada, _ = service.crear(_datos(ctx))

    assert service.obtener(creada.id).id == creada.id
    with pytest.raises(RecursoNoEncontrado):
        service.obtener(9999)


def test_registrar_muestra(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    consulta, _ = service.crear(_datos(ctx))

    muestra = service.registrar_muestra(
        consulta.id, MuestraCrear(tipo_muestra_id=ctx["tipo"])
    )

    assert muestra.consulta_id == consulta.id
    assert muestra.tipo_muestra_id == ctx["tipo"]
    assert muestra.estado_actual.nombre == "Extraida"
    assert muestra.fecha == consulta.fecha
    assert len(muestra.historial) == 1
    assert muestra.historial[0].estado.nombre == "Extraida"
    assert muestra.historial[0].responsable == "Eva"
    assert db.get(MuestraBiologica, muestra.id) is not None


def test_registrar_muestra_consulta_inexistente(db: Session, ctx: dict) -> None:
    with pytest.raises(RecursoNoEncontrado):
        ConsultaService(db).registrar_muestra(
            9999, MuestraCrear(tipo_muestra_id=ctx["tipo"])
        )


def test_registrar_muestra_tipo_inexistente(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    consulta, _ = service.crear(_datos(ctx))

    with pytest.raises(RecursoNoEncontrado):
        service.registrar_muestra(consulta.id, MuestraCrear(tipo_muestra_id=9999))

    assert service.listar_muestras(consulta.id) == []


def test_listar_muestras(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    consulta, _ = service.crear(_datos(ctx))
    otra, _ = service.crear(_datos(ctx, fecha=ctx["hoy"] - timedelta(days=2)))
    propia = service.registrar_muestra(
        consulta.id, MuestraCrear(tipo_muestra_id=ctx["tipo"])
    )
    service.registrar_muestra(otra.id, MuestraCrear(tipo_muestra_id=ctx["tipo"]))

    assert [muestra.id for muestra in service.listar_muestras(consulta.id)] == [propia.id]


def test_orden_derivacion_sin_muestras(db: Session, ctx: dict) -> None:
    consulta, _ = ConsultaService(db).crear(_datos(ctx))

    with pytest.raises(ConflictoDeRecurso):
        ConsultaService(db).orden_derivacion(consulta.id)


def test_orden_derivacion_pdf(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    consulta, _ = service.crear(_datos(ctx))
    service.registrar_muestra(consulta.id, MuestraCrear(tipo_muestra_id=ctx["tipo"]))

    contenido = service.orden_derivacion(consulta.id)

    assert isinstance(contenido, bytes)
    assert contenido.startswith(b"%PDF")
    assert len(contenido) > 0


def test_comprobante_pdf_con_y_sin_resultados(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    consulta, _ = service.crear(_datos(ctx))
    muestra = service.registrar_muestra(
        consulta.id, MuestraCrear(tipo_muestra_id=ctx["tipo"])
    )

    sin_resultado = service.comprobante(consulta.id)
    assert sin_resultado.startswith(b"%PDF")
    assert len(sin_resultado) > 0

    # El resultado se asigna directo: registrar_resultado es del bloque E.
    muestra.resultado = "Negativo"
    db.commit()
    con_resultado = service.comprobante(consulta.id)
    assert isinstance(con_resultado, bytes)
    assert con_resultado.startswith(b"%PDF")
    assert len(con_resultado) > 0


def test_costo_total_incluye_analisis(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    consulta, _ = service.crear(_datos(ctx, costo="100.00"))

    assert service.costo_total(consulta.id) == Decimal("100.00")

    service.registrar_muestra(consulta.id, MuestraCrear(tipo_muestra_id=ctx["tipo"]))
    assert service.costo_total(consulta.id) == Decimal("1600.00")


def test_consultas_inexistentes_en_resto_de_casos(db: Session, ctx: dict) -> None:
    service = ConsultaService(db)
    for metodo in (
        service.listar_muestras, service.orden_derivacion,
        service.comprobante, service.costo_total,
    ):
        with pytest.raises(RecursoNoEncontrado):
            metodo(9999)
