"""Selección de profesionales y pacientes, agenda y consultorio."""
from datetime import date

import flet as ft

from frontend.api import ErrorApi
from frontend.ui import Pantalla, campo, fila, opciones, requerido, seccion, selector, tabla


def seleccion(p: Pantalla) -> tuple[ft.Control, ft.Dropdown, ft.Dropdown]:
    """Limita el profesional al propio y carga mascotas del responsable elegido."""
    sesion = p.api.sesion
    clinica = selector("Clínica", p.api.consultar("clinicas"))
    vet = selector("Veterinario", [])
    cliente = selector("Cliente responsable", p.api.consultar("clientes"))
    mascota = selector("Mascota", [])

    def cargar(destino: ft.Dropdown, ruta: str) -> None:
        destino.options = []
        destino.value = None
        try:
            destino.options = opciones(p.api.consultar(ruta))
        except ErrorApi as error:
            p.error(error)
        p.page.update()

    clinica.on_select = lambda e: cargar(vet, f"clinicas/{clinica.value}/veterinarios")
    cliente.on_select = lambda e: cargar(mascota, f"clientes/{cliente.value}/mascotas")
    if sesion.rol == "VETERINARIO":
        perfil = p.api.consultar("auth/yo")
        clinica.value = str(perfil["clinica_id"])
        vet.options = opciones([{"id": sesion.veterinario_id, "nombre": perfil["veterinario_nombre"]}])
        vet.value = str(sesion.veterinario_id)
        clinica.disabled = vet.disabled = True
    return fila(clinica, vet, cliente, mascota), vet, mascota


def consultorio(p: Pantalla) -> None:
    """Registra la consulta y abre su ficha de derivación."""
    pacientes, vet, mascota = seleccion(p)
    fecha = campo("Fecha (AAAA-MM-DD)", value=date.today().isoformat())
    complejidad = selector("Complejidad", [{"id": k} for k in ("BAJA", "MEDIA", "ALTA")])
    costo = campo("Costo", hint_text="100.00")

    def registrar() -> None:
        consulta = p.api.pedir("POST", "consultas", {"veterinario_id": int(requerido(vet)),
            "mascota_id": int(requerido(mascota)), "fecha": fecha.value,
            "complejidad": requerido(complejidad), "costo": costo.value})
        p.ir(f"/consultas/{consulta['id']}")

    p.agregar(seccion("Registrar atención", pacientes, fila(fecha, complejidad, costo),
                      p.boton("Registrar consulta", registrar)))


def ficha(p: Pantalla, id_: int) -> None:
    """Muestra la atención, los importes, las derivaciones y los documentos."""
    ruta = f"consultas/{id_}"
    consulta = p.api.consultar(ruta)
    tipo = selector("Tipo de muestra", p.api.consultar("tipos-muestra"))
    pendientes = p.api.consultar(f"mascotas/{consulta['mascota_id']}/historia-clinica")
    vacunas = p.api.consultar(f"historias-clinicas/{pendientes['id']}/vacunas-pendientes")
    p.titulo.value = f"Consulta {consulta['numero']}"
    p.agregar(p.enlace("Volver al consultorio", "/consultorio"),
              seccion("Atención", tabla([consulta], ["fecha", "clinica_id", "mascota_id", "veterinario_id",
                                                     "complejidad", "costo"]),
                      ft.Text("Vacunas pendientes: " + (", ".join(v["nombre"] for v in vacunas) or "Ninguna"))),
              seccion("Muestras", tabla(p.api.consultar(f"{ruta}/muestras"), ["id", "fecha", "estado", "tipo_muestra_id"],
                      lambda m: p.enlace("Ver muestra", f"/muestras/{m['id']}")),
                      fila(tipo, p.boton("Agregar muestra", lambda: p.guardar(f"{ruta}/muestras",
                                                                             {"tipo_muestra_id": int(requerido(tipo))})))),
              seccion("Costo y documentos", tabla([p.api.consultar(f"{ruta}/costo-total")]),
                      fila(p.pdf("Orden de derivación PDF", f"{ruta}/orden-derivacion", f"orden-derivacion-{id_}.pdf"),
                           p.pdf("Comprobante PDF", f"{ruta}/comprobante", f"comprobante-{id_}.pdf"))))


def turnos(p: Pantalla) -> None:
    """Consulta agenda y disponibilidad y permite reservar o cancelar turnos."""
    pacientes, vet, mascota = seleccion(p)
    fecha = campo("Filtrar agenda por fecha (AAAA-MM-DD)")
    inicio = campo("Inicio", hint_text="AAAA-MM-DD HH:MM")
    fin = campo("Fin", hint_text="AAAA-MM-DD HH:MM")
    agenda, disponible = ft.Column(), ft.Text()

    def ruta() -> str:
        return f"veterinarios/{requerido(vet)}"

    def cargar() -> None:
        datos = p.api.consultar(f"{ruta()}/agenda", fecha=fecha.value)
        agenda.controls = [tabla(datos, ["id", "mascota_id", "inicio", "fin", "activo"],
            lambda t: p.boton("Cancelar", lambda: cancelar(t["id"])) if t["activo"] else ft.Text("Cancelado"))]

    def cancelar(id_: int) -> None:
        p.api.pedir("DELETE", f"turnos/{id_}")
        cargar()

    def intervalo() -> dict:
        return {"inicio": requerido(inicio).replace(" ", "T"), "fin": requerido(fin).replace(" ", "T")}

    def verificar() -> None:
        datos = p.api.consultar(f"{ruta()}/turnos/disponibilidad", **intervalo())
        disponible.value = "Intervalo disponible." if datos["disponible"] else "Intervalo ocupado."

    def reservar() -> None:
        p.api.pedir("POST", f"{ruta()}/turnos", dict(intervalo(), mascota_id=int(requerido(mascota))))
        disponible.value = "Turno registrado."
        cargar()

    p.agregar(seccion("Profesional y paciente", pacientes),
              seccion("Agenda", fila(fecha, p.boton("Ver agenda", cargar)), agenda),
              seccion("Reservar turno", fila(inicio, fin), fila(p.boton("Consultar disponibilidad", verificar),
                      p.boton("Crear turno", reservar)), disponible))
    if vet.value:
        cargar()
