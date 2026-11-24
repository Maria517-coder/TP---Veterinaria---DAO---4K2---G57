"""Carga datos de demostración para la defensa.

Ejecutar desde backend/:
    python -m app.seeds.datos_demo

No se ejecuta al iniciar la app ni en tests de otros módulos.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import SessionLocal, crear_tablas
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.especie import Especie
from app.models.tipo_muestra import TipoMuestra
from app.schemas.cliente import ClienteCrear
from app.schemas.clinica import ClinicaVeterinariaCrear
from app.schemas.consulta import ConsultaCrear, MuestraCrear
from app.schemas.contenedor import ContenedorCrear, MuestraAgregar, RemitoGenerar
from app.schemas.mascota import MascotaCrear
from app.schemas.muestra import ResultadoCrear
from app.schemas.remito import ResponsableAccion
from app.schemas.turno import TurnoCrear
from app.schemas.vacuna import VacunaCrear, VacunacionCrear
from app.schemas.veterinario import AccesoVeterinario, VeterinarioCrear
from app.seeds.datos_iniciales import cargar_datos_iniciales
from app.services.cliente_service import ClienteService
from app.services.clinica_service import ClinicaService
from app.services.consulta_service import ConsultaService
from app.services.contenedor_service import ContenedorService
from app.services.mascota_service import MascotaService
from app.services.muestra_service import MuestraService
from app.services.remito_service import RemitoService
from app.services.turno_service import TurnoService
from app.services.usuario_service import UsuarioService
from app.services.vacuna_service import VacunaService
from app.services.veterinario_service import VeterinarioService


CLINICA_CENTRAL = "Clínica Central"
CLINICA_NORTE = "Clínica Norte"


def _id_por_nombre(db: Session, modelo: type, nombre: str) -> int:
    valor = db.scalar(select(modelo.id).where(modelo.nombre == nombre))
    if valor is None:
        raise ValueError(f"No existe {modelo.__name__} con nombre '{nombre}'")
    return int(valor)


def _fecha_consulta() -> date:
    hoy = date.today()
    # Dentro del mes actual y no futura.
    return hoy


def cargar_datos_demo(db: Session) -> dict | None:
    """Crea datos de demo si no existen. Devuelve resumen o None si ya estaban."""
    existe = db.scalar(
        select(ClinicaVeterinaria.id).where(ClinicaVeterinaria.nombre == CLINICA_CENTRAL)
    )
    if existe is not None:
        print("Datos de demo ya existen (se encontró 'Clínica Central'). No se duplicó nada.")
        return None

    cargar_datos_iniciales(db)
    db.commit()

    clinica_srv = ClinicaService(db)
    vet_srv = VeterinarioService(db)
    cliente_srv = ClienteService(db)
    mascota_srv = MascotaService(db)
    vacuna_srv = VacunaService(db)
    consulta_srv = ConsultaService(db)
    contenedor_srv = ContenedorService(db)
    remito_srv = RemitoService(db)
    muestra_srv = MuestraService(db)
    turno_srv = TurnoService(db)

    # Clínicas
    central = clinica_srv.agregar_clinica_a_red(ClinicaVeterinariaCrear(nombre=CLINICA_CENTRAL))
    norte = clinica_srv.agregar_clinica_a_red(ClinicaVeterinariaCrear(nombre=CLINICA_NORTE))

    # Veterinarios (2 en Central, 1 en Norte). vet1 vinculado a veterinario real.
    vet1 = vet_srv.crear_en_clinica(
        central.id,
        VeterinarioCrear(
            matricula="MP-DEMO-001",
            nombre="Dra. Ana Demo",
            acceso=AccesoVeterinario(nombre_usuario="vet1", contrasena="vet12345"),
        ),
    )
    vet2 = vet_srv.crear_en_clinica(
        central.id,
        VeterinarioCrear(matricula="MP-DEMO-002", nombre="Dr. Bruno Demo"),
    )
    vet3 = vet_srv.crear_en_clinica(
        norte.id,
        VeterinarioCrear(matricula="MP-DEMO-003", nombre="Dra. Carla Norte"),
    )

    # Especies y tipos de muestra
    perro_id = _id_por_nombre(db, Especie, "PERRO")
    gato_id = _id_por_nombre(db, Especie, "GATO")
    tipo_sangre = _id_por_nombre(db, TipoMuestra, "SANGRE")
    tipo_orina = _id_por_nombre(db, TipoMuestra, "ORINA")
    tipo_heces = _id_por_nombre(db, TipoMuestra, "HECES")
    tipo_hisopado = _id_por_nombre(db, TipoMuestra, "HISOPADO")
    tipo_tejido = _id_por_nombre(db, TipoMuestra, "TEJIDO")

    # Clientes
    cliente1 = cliente_srv.crear(ClienteCrear(nombre="Juan Pérez", telefono="3511111111"))
    cliente2 = cliente_srv.crear(ClienteCrear(nombre="María Gómez", telefono="3512222222"))
    cliente3 = cliente_srv.crear(ClienteCrear(nombre="Lucía Torres", telefono="3513333333"))

    # Mascotas (4: perros y gatos)
    mascota1 = mascota_srv.crear(
        MascotaCrear(cliente_id=cliente1.id, especie_id=perro_id, nombre="Fido", fecha_nacimiento=date(2020, 5, 10))
    )
    mascota2 = mascota_srv.crear(
        MascotaCrear(cliente_id=cliente1.id, especie_id=gato_id, nombre="Mishi", fecha_nacimiento=date(2021, 3, 15))
    )
    mascota3 = mascota_srv.crear(
        MascotaCrear(cliente_id=cliente2.id, especie_id=perro_id, nombre="Luna", fecha_nacimiento=date(2019, 8, 20))
    )
    mascota4 = mascota_srv.crear(
        MascotaCrear(cliente_id=cliente3.id, especie_id=gato_id, nombre="Nala", fecha_nacimiento=date(2022, 1, 5))
    )

    # Vacunas catálogo (obligatorias para perro y gato)
    rabia = vacuna_srv.crear(VacunaCrear(nombre="Rabia", obligatoria=True, especies_aplicables=[perro_id, gato_id]))
    parvo = vacuna_srv.crear(VacunaCrear(nombre="Parvovirus", obligatoria=True, especies_aplicables=[perro_id, gato_id]))

    # mascota1 (perro) con carnet completo: aplica todas las obligatorias
    mascota_srv.registrar_vacunacion(mascota1.historia_clinica.id, VacunacionCrear(vacuna_id=rabia.id, fecha=date(2024, 1, 10)))
    mascota_srv.registrar_vacunacion(mascota1.historia_clinica.id, VacunacionCrear(vacuna_id=parvo.id, fecha=date(2024, 1, 10)))
    # mascota2 (gato) con pendientes: no se le aplican obligatorias

    fecha = _fecha_consulta()

    # Consultas dentro del mes actual, costo texto "100.00"
    # mascota2 tiene vacunas pendientes -> aviso al registrar consulta
    consulta_pendiente, pendientes = consulta_srv.crear(
        ConsultaCrear(
            veterinario_id=vet1.id, mascota_id=mascota2.id, fecha=fecha,
            complejidad="BAJA", costo="100.00",
        )
    )
    consulta_central_2, _ = consulta_srv.crear(
        ConsultaCrear(
            veterinario_id=vet1.id, mascota_id=mascota1.id, fecha=fecha,
            complejidad="MEDIA", costo="100.00",
        )
    )
    consulta_norte_1, _ = consulta_srv.crear(
        ConsultaCrear(
            veterinario_id=vet3.id, mascota_id=mascota4.id, fecha=fecha,
            complejidad="BAJA", costo="100.00",
        )
    )
    consulta_norte_2, _ = consulta_srv.crear(
        ConsultaCrear(
            veterinario_id=vet3.id, mascota_id=mascota3.id, fecha=fecha,
            complejidad="ALTA", costo="100.00",
        )
    )
    consulta_central_3, _ = consulta_srv.crear(
        ConsultaCrear(
            veterinario_id=vet2.id, mascota_id=mascota3.id, fecha=fecha,
            complejidad="BAJA", costo="100.00",
        )
    )
    consulta_norte_3, _ = consulta_srv.crear(
        ConsultaCrear(
            veterinario_id=vet3.id, mascota_id=mascota2.id, fecha=fecha,
            complejidad="BAJA", costo="100.00",
        )
    )

    # Muestras en 6 estados por camino real. Mezclar 2 clínicas, sin mezclar dentro de un contenedor.
    # 1) Extraída sin contenedor (Central)
    m_extraida = consulta_srv.registrar_muestra(consulta_central_2.id, MuestraCrear(tipo_muestra_id=tipo_sangre))

    # 2) Empaquetada: contenedor sin remito (Norte)
    m_empaquetada = consulta_srv.registrar_muestra(consulta_norte_1.id, MuestraCrear(tipo_muestra_id=tipo_orina))
    cont_emp = contenedor_srv.crear(ContenedorCrear())
    contenedor_srv.agregar_muestra(cont_emp.id, MuestraAgregar(muestra_id=m_empaquetada.id, responsable="Recepción"))

    # 3) En tránsito: remito despachado (Central)
    m_transito = consulta_srv.registrar_muestra(consulta_central_3.id, MuestraCrear(tipo_muestra_id=tipo_heces))
    cont_transito = contenedor_srv.crear(ContenedorCrear())
    contenedor_srv.agregar_muestra(cont_transito.id, MuestraAgregar(muestra_id=m_transito.id, responsable="Recepción"))
    remito_transito = contenedor_srv.generar_remito(cont_transito.id, RemitoGenerar(laboratorio_destino="Laboratorio Central"))
    remito_srv.despachar(remito_transito.id, ResponsableAccion(responsable="Transporte"))

    # 4) Recibida: remito recibido, lista para cargar resultado (Norte)
    m_recibida = consulta_srv.registrar_muestra(consulta_norte_2.id, MuestraCrear(tipo_muestra_id=tipo_hisopado))
    cont_recibida = contenedor_srv.crear(ContenedorCrear())
    contenedor_srv.agregar_muestra(cont_recibida.id, MuestraAgregar(muestra_id=m_recibida.id, responsable="Recepción"))
    remito_recibida = contenedor_srv.generar_remito(cont_recibida.id, RemitoGenerar(laboratorio_destino="Laboratorio Central"))
    remito_srv.despachar(remito_recibida.id, ResponsableAccion(responsable="Transporte"))
    remito_srv.recepcionar(remito_recibida.id, ResponsableAccion(responsable="Laboratorio"))

    # 5) Analizada: con resultado, remito cerrado automáticamente (Central)
    m_analizada = consulta_srv.registrar_muestra(consulta_pendiente.id, MuestraCrear(tipo_muestra_id=tipo_tejido))
    cont_analizada = contenedor_srv.crear(ContenedorCrear())
    contenedor_srv.agregar_muestra(cont_analizada.id, MuestraAgregar(muestra_id=m_analizada.id, responsable="Recepción"))
    remito_analizada = contenedor_srv.generar_remito(cont_analizada.id, RemitoGenerar(laboratorio_destino="Laboratorio Central"))
    remito_srv.despachar(remito_analizada.id, ResponsableAccion(responsable="Transporte"))
    remito_srv.recepcionar(remito_analizada.id, ResponsableAccion(responsable="Laboratorio"))
    muestra_srv.registrar_resultado(m_analizada.id, ResultadoCrear(texto="Resultado demo normal", responsable="Dra. Lab"))

    # 6) Rechazada: contenedor con precinto roto (Norte)
    m_rechazada = consulta_srv.registrar_muestra(consulta_norte_3.id, MuestraCrear(tipo_muestra_id=tipo_sangre))
    cont_rechazada = contenedor_srv.crear(ContenedorCrear())
    contenedor_srv.agregar_muestra(cont_rechazada.id, MuestraAgregar(muestra_id=m_rechazada.id, responsable="Recepción"))
    remito_rechazada = contenedor_srv.generar_remito(cont_rechazada.id, RemitoGenerar(laboratorio_destino="Laboratorio Central"))
    remito_srv.despachar(remito_rechazada.id, ResponsableAccion(responsable="Transporte"))
    contenedor_srv.romper_precinto(cont_rechazada.id)
    remito_srv.recepcionar(remito_rechazada.id, ResponsableAccion(responsable="Laboratorio"))

    # Turnos futuros para distintos veterinarios, anclados a 10:00 del día siguiente
    manana_10 = datetime.combine(date.today() + timedelta(days=1), time(10, 0))
    turno_srv.crear(vet1.id, TurnoCrear(mascota_id=mascota1.id, inicio=manana_10, fin=manana_10 + timedelta(minutes=30)))
    turno_srv.crear(vet2.id, TurnoCrear(mascota_id=mascota3.id, inicio=manana_10 + timedelta(hours=1), fin=manana_10 + timedelta(hours=1, minutes=30)))
    turno_srv.crear(vet3.id, TurnoCrear(mascota_id=mascota4.id, inicio=manana_10 + timedelta(hours=2), fin=manana_10 + timedelta(hours=2, minutes=30)))

    resumen = {
        "clinicas": [CLINICA_CENTRAL, CLINICA_NORTE],
        "veterinarios": [
            {"nombre": vet1.nombre, "matricula": vet1.matricula, "clinica": CLINICA_CENTRAL},
            {"nombre": vet2.nombre, "matricula": vet2.matricula, "clinica": CLINICA_CENTRAL},
            {"nombre": vet3.nombre, "matricula": vet3.matricula, "clinica": CLINICA_NORTE},
        ],
        "credenciales": {
            "admin": {"usuario": "admin", "contrasena": "(la configurada por ADMIN_PASSWORD, por defecto admin123)"},
            "veterinario": {"usuario": "vet1", "contrasena": "vet12345"},
        },
        "muestras_estados": [
            "Extraida", "Empaquetada", "EnTransito", "Recibida", "Analizada", "Rechazada"
        ],
    }
    return resumen


def main() -> None:
    crear_tablas()
    with SessionLocal() as db:
        with db.begin():
            cargar_datos_iniciales(db)
    with SessionLocal() as db:
        UsuarioService(db).asegurar_admin_inicial("admin123")
    with SessionLocal() as db:
        resumen = cargar_datos_demo(db)
    if resumen is None:
        return
    print("\n=== Datos de demo cargados ===")
    print(f"Clínicas: {', '.join(resumen['clinicas'])}")
    print("Veterinarios:")
    for v in resumen["veterinarios"]:
        print(f"  - {v['nombre']} ({v['matricula']}) - {v['clinica']}")
    print("Credenciales:")
    print(f"  - admin / {resumen['credenciales']['admin']['contrasena']}")
    print(f"  - {resumen['credenciales']['veterinario']['usuario']} / {resumen['credenciales']['veterinario']['contrasena']}")
    print(f"Muestras en estados: {', '.join(resumen['muestras_estados'])}")


if __name__ == "__main__":
    main()
