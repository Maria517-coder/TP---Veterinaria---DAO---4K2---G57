"""Clientes, mascotas, historia clínica y vacunaciones."""
import flet as ft

from frontend.ui import Pantalla, campo, fila, requerido, seccion, selector, tabla

# TODO: usar el catálogo del backend cuando exista GET /api/especies.
ESPECIES = [{"id": 1, "nombre": "PERRO"}, {"id": 2, "nombre": "GATO"}, {"id": 3, "nombre": "OTRO"}]


def recepcion(p: Pantalla) -> None:
    """Registra clientes, mascotas y vacunas y permite buscar por responsable."""
    clientes = p.api.consultar("clientes")
    mascotas = p.api.consultar("mascotas")
    responsables = {c["id"]: c["nombre"] for c in clientes}
    especies = {e["id"]: e["nombre"] for e in ESPECIES}
    nombre, telefono = campo("Nombre y apellido"), campo("Teléfono")
    p.agregar(seccion("Nuevo cliente", fila(nombre, telefono), p.boton("Crear cliente",
        lambda: p.guardar("clientes", {"nombre": nombre.value, "telefono": telefono.value}))))
    cliente, especie = selector("Cliente responsable", clientes), selector("Especie", ESPECIES)
    mascota, fecha = campo("Nombre de la mascota"), campo("Nacimiento (AAAA-MM-DD)")
    p.agregar(seccion("Nueva mascota", fila(cliente, especie, mascota, fecha), p.boton("Crear mascota",
        lambda: p.guardar("mascotas", {"cliente_id": int(requerido(cliente)), "especie_id": int(requerido(especie)),
                                      "nombre": mascota.value, "fecha_nacimiento": fecha.value}))))
    vacuna = campo("Nombre de la vacuna")
    obligatoria = ft.Checkbox(label="Obligatoria")
    checks = [(e["id"], ft.Checkbox(label=e["nombre"])) for e in ESPECIES]
    p.agregar(seccion("Catálogo de vacunas", fila(vacuna, obligatoria, *(c for _, c in checks)),
        p.boton("Cargar vacuna", lambda: p.guardar("vacunas", {
            "nombre": vacuna.value, "obligatoria": bool(obligatoria.value),
            "especies_aplicables": [id_ for id_, c in checks if c.value]}))))
    p.agregar(seccion("Clientes", tabla(clientes, ["id", "nombre", "telefono"])))
    buscar = campo("Buscar mascota o responsable")
    listado = ft.Column()

    def filtrar(e: ft.Event | None = None) -> None:
        termino = (buscar.value or "").casefold().strip()
        datos = [dict(m, responsable=responsables.get(m["cliente_id"], ""), especie=especies.get(m["especie_id"]))
                 for m in mascotas]
        listado.controls = [tabla([m for m in datos if termino in m["nombre"].casefold()
                                   or termino in m["responsable"].casefold()],
                                  ["id", "nombre", "responsable", "especie"],
                                  lambda m: p.enlace("Ver ficha", f"/mascotas/{m['id']}"))]
        if e:
            p.page.update()

    buscar.on_change = filtrar
    filtrar()
    p.agregar(seccion("Mascotas", buscar, listado))


def ficha(p: Pantalla, id_: int) -> None:
    """Consulta la historia, el carnet, las vacunas, las consultas y los turnos."""
    mascota = p.api.consultar(f"mascotas/{id_}")
    historia = p.api.consultar(f"mascotas/{id_}/historia-clinica")
    cliente = p.api.consultar(f"clientes/{mascota['cliente_id']}")
    ruta = f"historias-clinicas/{historia['id']}"
    p.titulo.value = mascota["nombre"]
    p.agregar(p.enlace("Volver a recepción", "/recepcion"),
              seccion("Historia clínica", tabla([dict(mascota, historia=historia["numero"],
                      responsable=cliente["nombre"], especie=next((e["nombre"] for e in ESPECIES
                      if e["id"] == mascota["especie_id"]), mascota["especie_id"]))],
                      ["historia", "responsable", "especie", "fecha_nacimiento", "activo"]),
                      p.pdf("Descargar carnet PDF", f"mascotas/{id_}/carnet-vacunas", f"carnet-vacunas-{id_}.pdf")))
    vacunas = p.api.consultar("vacunas")
    nombres = {v["id"]: v["nombre"] for v in vacunas}
    pendientes = p.api.consultar(f"{ruta}/vacunas-pendientes")
    aplicadas = p.api.consultar(f"{ruta}/vacunaciones")
    vacuna, fecha = selector("Vacuna", vacunas), campo("Fecha (AAAA-MM-DD)")
    p.agregar(seccion("Vacunas pendientes", tabla(pendientes, ["nombre"])),
              seccion("Vacunaciones", tabla([dict(v, vacuna=nombres.get(v["vacuna_id"])) for v in aplicadas],
                                            ["vacuna", "fecha"]), fila(vacuna, fecha),
                      p.boton("Registrar vacunación", lambda: p.guardar(f"{ruta}/vacunaciones",
                              {"vacuna_id": int(requerido(vacuna)), "fecha": fecha.value}))),
              seccion("Consultas", tabla(p.api.consultar("consultas", mascota_id=id_),
                      ["numero", "fecha", "complejidad", "costo"],
                      lambda c: p.enlace("Ver consulta", f"/consultas/{c['id']}"))))
    turnos = ft.Column()

    def cargar_turnos() -> None:
        if p.api.sesion.rol == "VETERINARIO":
            veterinarios = [p.api.consultar("auth/yo")]
            vets = [(v["veterinario_id"], v["veterinario_nombre"]) for v in veterinarios]
        else:
            vets = [(v["id"], v["nombre"]) for c in p.api.consultar("clinicas")
                    for v in p.api.consultar(f"clinicas/{c['id']}/veterinarios")]
        datos = [dict(t, veterinario=nombre) for vet_id, nombre in vets
                 for t in p.api.consultar(f"veterinarios/{vet_id}/agenda") if t["mascota_id"] == id_]
        turnos.controls = [tabla(datos, ["veterinario", "inicio", "fin", "activo"])]

    p.agregar(seccion("Turnos de la mascota", p.boton("Cargar turnos", cargar_turnos), turnos))
