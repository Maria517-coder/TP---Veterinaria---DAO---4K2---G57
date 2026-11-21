"""Reglas propias de ContenedorEnvio: muestras, remito, precinto y finalización."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, ReglaDeNegocioViolada
from app.models import (
    Cliente,
    ClinicaVeterinaria,
    Complejidad,
    ConsultaMedica,
    ContenedorEnvio,
    Especie,
    EstadoCatalogo,
    EstadoRemito,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    RemitoBiologico,
    TipoMuestra,
    Veterinario,
)
from app.models.estados import (
    Analizada,
    Empaquetada,
    EnTransito,
    Rechazada,
    Recibida,
)
from app.seeds.datos_iniciales import cargar_datos_iniciales


@pytest.fixture()
def ctx(db: Session) -> dict:
    """Prepara catálogos, dos clínicas y una fábrica de muestras con fechas relativas."""
    cargar_datos_iniciales(db)
    db.commit()
    red = db.scalar(select(RedVeterinaria))
    tipo = db.scalar(select(TipoMuestra).where(TipoMuestra.nombre == "SANGRE"))
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    estados = {fila.nombre: fila for fila in db.scalars(select(EstadoCatalogo))}
    hoy = datetime.now().date()

    clinicas = [
        ClinicaVeterinaria(nombre="Centro", red=red),
        ClinicaVeterinaria(nombre="Oeste", red=red),
    ]
    responsable = Cliente(nombre="Ana", telefono="123")
    db.add_all([*clinicas, responsable])
    db.flush()

    consultas = []
    for indice, clinica in enumerate(clinicas, start=1):
        veterinario = Veterinario(
            nombre=f"Vet{indice}", matricula=f"MP-T1-{indice}", clinica=clinica
        )
        mascota = Mascota(
            nombre=f"M{indice}",
            fecha_nacimiento=hoy - timedelta(days=365 * 3),
            responsable=responsable,
            especie=especie,
            historia_clinica=HistoriaClinica(numero=indice),
        )
        db.add_all([veterinario, mascota])
        db.flush()
        consulta = ConsultaMedica(
            numero=indice,
            clinica=clinica,
            mascota=mascota,
            veterinario=veterinario,
            fecha=hoy,
            complejidad=Complejidad.BAJA,
            costo=Decimal("100.00"),
        )
        db.add(consulta)
        db.flush()
        consultas.append(consulta)
    db.commit()

    def nueva(consulta: ConsultaMedica, estado: str = "Extraida") -> MuestraBiologica:
        muestra = MuestraBiologica(
            consulta=consulta,
            tipo=tipo,
            estado_actual=estados[estado],
            fecha=datetime.now().date(),
        )
        db.add(muestra)
        db.flush()
        return muestra

    return {
        "db": db,
        "estados": estados,
        "clinicas": clinicas,
        "consultas": consultas,
        "nueva": nueva,
    }


def test_agregar_muestra_valida_y_pasa_a_empaquetada(ctx: dict) -> None:
    db: Session = ctx["db"]
    contenedor = ContenedorEnvio(numero=1, precinto_intacto=True)
    db.add(contenedor)
    db.flush()
    muestra = ctx["nueva"](ctx["consultas"][0])

    contenedor.agregar_muestra(muestra, "Eva")
    db.flush()

    assert muestra.contenedor is contenedor
    assert muestra.contenedor_id == contenedor.id
    assert isinstance(muestra.estado, Empaquetada)
    assert [registro.estado.nombre for registro in muestra.historial] == ["Empaquetada"]
    assert muestra.historial[0].responsable == "Eva"


def test_agregar_muestra_rechaza_otra_clinica_y_estado_distinto(ctx: dict) -> None:
    db: Session = ctx["db"]
    contenedor = ContenedorEnvio(numero=1)
    db.add(contenedor)
    db.flush()
    contenedor.agregar_muestra(ctx["nueva"](ctx["consultas"][0]), "Eva")

    de_otra_clinica = ctx["nueva"](ctx["consultas"][1])
    with pytest.raises(ReglaDeNegocioViolada, match="misma clínica"):
        contenedor.agregar_muestra(de_otra_clinica, "Eva")
    assert de_otra_clinica.contenedor_id is None
    assert de_otra_clinica.historial == []

    ya_en_transito = ctx["nueva"](ctx["consultas"][0], "EnTransito")
    with pytest.raises(ConflictoDeRecurso, match="Extraida"):
        contenedor.agregar_muestra(ya_en_transito, "Eva")
    assert ya_en_transito.contenedor_id is None
    assert ya_en_transito.historial == []


def test_romper_precinto_es_irreversible(ctx: dict) -> None:
    db: Session = ctx["db"]
    contenedor = ContenedorEnvio(numero=1)
    db.add(contenedor)
    db.flush()

    contenedor.romper_precinto()
    assert contenedor.precinto_intacto is False

    with pytest.raises(ConflictoDeRecurso, match="ya está roto"):
        contenedor.romper_precinto()
    assert contenedor.precinto_intacto is False


@pytest.mark.parametrize(
    "estado,numero",
    [(EstadoRemito.RECIBIDO, 11), (EstadoRemito.CERRADO, 12)],
)
def test_romper_precinto_se_bloquea_despues_de_la_recepcion(
    ctx: dict, estado: EstadoRemito, numero: int
) -> None:
    db: Session = ctx["db"]
    contenedor = ContenedorEnvio(numero=numero)
    db.add(contenedor)
    db.flush()
    remito = RemitoBiologico(
        numero=numero,
        fecha_emision=datetime.now(),
        clinica_origen_id=ctx["clinicas"][0].id,
        laboratorio_destino="Lab",
        estado=estado,
        contenedor=contenedor,
    )
    db.add(remito)
    db.flush()

    with pytest.raises(ConflictoDeRecurso, match="recepción"):
        contenedor.romper_precinto()
    assert contenedor.precinto_intacto is True


def test_generar_remito_exige_muestras_y_crea_generado(ctx: dict) -> None:
    db: Session = ctx["db"]
    contenedor = ContenedorEnvio(numero=1)
    db.add(contenedor)
    db.flush()

    with pytest.raises(ConflictoDeRecurso, match="no tiene muestras"):
        contenedor.generar_remito("Lab Norte", 7)

    contenedor.agregar_muestra(ctx["nueva"](ctx["consultas"][0]), "Eva")
    antes = datetime.now()
    remito = contenedor.generar_remito("Lab Norte", 7)
    despues = datetime.now()
    db.add(remito)
    db.flush()

    assert remito.estado is EstadoRemito.GENERADO
    assert remito.numero == 7
    assert remito.laboratorio_destino == "Lab Norte"
    assert remito.clinica_origen_id == ctx["clinicas"][0].id
    assert remito.contenedor is contenedor
    assert contenedor.remito is remito
    assert antes <= remito.fecha_emision <= despues

    with pytest.raises(ConflictoDeRecurso, match="ya tiene un remito"):
        contenedor.generar_remito("Otro lab", 8)


def test_todas_muestras_finalizadas_solo_con_estados_finales(ctx: dict) -> None:
    db: Session = ctx["db"]
    contenedor = ContenedorEnvio(numero=1)
    db.add(contenedor)
    db.flush()
    assert contenedor.todas_muestras_finalizadas() is False

    primera = ctx["nueva"](ctx["consultas"][0])
    contenedor.agregar_muestra(primera, "Eva")
    primera.cambiar_estado(EnTransito(), "Eva")
    primera.cambiar_estado(Recibida(), "Eva")
    assert contenedor.todas_muestras_finalizadas() is False

    primera.cambiar_estado(Analizada(), "Lab")
    assert contenedor.todas_muestras_finalizadas() is True

    segunda = ctx["nueva"](ctx["consultas"][0])
    contenedor.agregar_muestra(segunda, "Eva")
    assert contenedor.todas_muestras_finalizadas() is False

    segunda.cambiar_estado(EnTransito(), "Eva")
    segunda.cambiar_estado(Rechazada(), "Eva")
    assert contenedor.todas_muestras_finalizadas() is True
