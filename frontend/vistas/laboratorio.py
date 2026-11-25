"""Trazabilidad de muestras, contenedores y remitos."""
import flet as ft

from frontend.ui import Pantalla, campo, fila, requerido, seccion, selector, tabla


def lista_muestras(p: Pantalla, **filtros: object) -> ft.Control:
    """Vincula las muestras encontradas a su historial."""
    return tabla(p.api.consultar("muestras", **filtros),
                 ["id", "consulta_id", "tipo_muestra_id", "estado", "fecha", "contenedor_id"],
                 lambda m: p.enlace("Ver muestra", f"/muestras/{m['id']}"))


def laboratorio(p: Pantalla) -> None:
    """Busca muestras y remitos y permite crear contenedores."""
    estados = ("Extraida", "Empaquetada", "EnTransito", "Recibida", "Analizada", "Rechazada")
    estado = selector("Estado de la muestra", [{"id": k} for k in estados], opcional=True)
    clinica = selector("Clínica", p.api.consultar("clinicas"), opcional=True)
    fecha = campo("Fecha (AAAA-MM-DD)")
    muestras = ft.Column()
    remitos = ft.Column()
    tramite = selector("Estado del remito", [{"id": k} for k in ("GENERADO", "DESPACHADO", "RECIBIDO", "CERRADO")],
                      opcional=True)
    desde, hasta = campo("Desde (AAAA-MM-DD)"), campo("Hasta (AAAA-MM-DD)")

    def buscar_muestras() -> None:
        muestras.controls = [lista_muestras(p, estado=estado.value, clinica_id=clinica.value, fecha=fecha.value)]

    def buscar_remitos() -> None:
        datos = p.api.consultar("remitos", estado=tramite.value, desde=desde.value, hasta=hasta.value)
        remitos.controls = [tabla(datos, ["numero", "estado", "laboratorio_destino", "fecha_emision"],
                                  lambda r: p.enlace("Ver remito", f"/remitos/{r['id']}"))]

    buscar_muestras()
    buscar_remitos()
    p.agregar(seccion("Muestras", fila(estado, clinica, fecha), p.boton("Buscar muestras", buscar_muestras), muestras),
              seccion("Contenedores", p.boton("Crear contenedor", lambda: p.guardar("contenedores", {}, "contenedores")),
                      tabla(p.api.consultar("contenedores"), ["numero", "precinto_intacto", "cantidad_muestras", "remito_id"],
                            lambda c: p.enlace("Ver contenedor", f"/contenedores/{c['id']}"))),
              seccion("Remitos", fila(tramite, desde, hasta), p.boton("Buscar remitos", buscar_remitos), remitos))


def contenedor(p: Pantalla, id_: int) -> None:
    """Gestiona precinto, incorporación de muestras y emisión del remito."""
    ruta = f"contenedores/{id_}"
    datos = p.api.consultar(ruta)
    p.titulo.value = f"Contenedor {datos['numero']}"
    p.agregar(p.enlace("Volver a laboratorio", "/laboratorio"), tabla([datos]),
              seccion("Muestras del contenedor", lista_muestras(p, contenedor_id=id_)))
    if datos["precinto_intacto"]:
        p.agregar(p.boton("Romper precinto", lambda: p.guardar(f"{ruta}/romper-precinto", {})))
    if datos["remito_id"]:
        p.agregar(p.enlace("Ver remito", f"/remitos/{datos['remito_id']}"))
        return
    opciones = [dict(m, nombre=f"Muestra {m['id']} · Consulta {m['consulta_id']} · Tipo {m['tipo_muestra_id']}")
                for m in p.api.consultar("muestras", estado="Extraida") if not m["contenedor_id"]]
    muestra = selector("Muestra extraída", opciones)
    responsable, destino = campo("Responsable"), campo("Laboratorio destino")
    p.agregar(seccion("Agregar muestra", fila(muestra, responsable), p.boton("Agregar al contenedor",
                      lambda: p.guardar(f"{ruta}/muestras", {"muestra_id": int(requerido(muestra)),
                                                            "responsable": responsable.value}))),
              seccion("Generar remito", destino, p.boton("Generar remito", lambda: p.guardar(f"{ruta}/remito",
                      {"laboratorio_destino": destino.value}, "remitos"))))


def remito(p: Pantalla, id_: int) -> None:
    """Presenta acciones habilitadas por estado y documentos del envío."""
    ruta = f"remitos/{id_}"
    datos = p.api.consultar(ruta)
    p.titulo.value = f"Remito {datos['numero']}"
    p.agregar(p.enlace("Volver a laboratorio", "/laboratorio"), tabla([datos]),
              seccion("Muestras del remito", lista_muestras(p, contenedor_id=datos["contenedor_id"])))
    acciones = {"GENERADO": ("Despachar remito", "despachar"), "DESPACHADO": ("Registrar recepción", "recepcion")}
    if datos["estado"] in acciones:
        etiqueta, operacion = acciones[datos["estado"]]
        responsable = campo("Responsable")
        p.agregar(seccion(etiqueta, responsable, p.boton(etiqueta, lambda: p.guardar(
            f"{ruta}/{operacion}", {"responsable": responsable.value}))))
    resultado = ft.Text()

    def transito() -> None:
        segundos = p.api.consultar(f"{ruta}/tiempo-transito")["tiempo_transito"]
        resultado.value = f"Tiempo de tránsito: {segundos} segundos."

    p.agregar(fila(p.pdf("Descargar PDF", f"{ruta}/imprimir", f"remito-{id_}.pdf"),
                   p.boton("Ver tiempo de tránsito", transito)), resultado)


def muestra(p: Pantalla, id_: int) -> None:
    """Muestra la historia y registra el resultado de una muestra recibida."""
    ruta = f"muestras/{id_}"
    datos = p.api.consultar(ruta)
    p.titulo.value = f"Muestra {id_}"
    p.agregar(p.enlace("Volver a laboratorio", "/laboratorio"), tabla([datos]),
              seccion("Historial de estados", tabla(p.api.consultar(f"{ruta}/historial-estados"),
                                                    ["estado", "fecha_hora", "responsable"])))
    if datos["estado"] == "Recibida":
        texto, responsable = campo("Resultado", multiline=True), campo("Responsable")
        p.agregar(seccion("Resultado del análisis", fila(texto, responsable),
                          p.boton("Registrar resultado", lambda: p.guardar(f"{ruta}/resultado",
                                 {"texto": texto.value, "responsable": responsable.value}))))
