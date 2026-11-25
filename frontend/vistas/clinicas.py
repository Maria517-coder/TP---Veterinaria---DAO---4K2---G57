"""Clínicas, veterinarios y atención por sede."""
import flet as ft

from frontend.ui import Pantalla, campo, fila, seccion, tabla
from frontend.vistas.reportes import panel_reporte


def clinicas(p: Pantalla) -> None:
    """Lista clínicas y permite el alta al administrador."""
    if p.api.sesion.rol == "ADMIN":
        nombre = campo("Nombre de la clínica")
        p.agregar(seccion("Nueva clínica", fila(nombre, p.boton("Crear clínica",
            lambda: p.guardar("red/clinicas", {"nombre": nombre.value})))))
    p.agregar(seccion("Clínicas registradas", tabla(p.api.consultar("clinicas"), ["id", "nombre"],
        lambda c: p.enlace("Ver ficha", f"/clinicas/{c['id']}"))))


def ficha(p: Pantalla, id_: int) -> None:
    """Muestra profesionales, consultas y facturación de la sede."""
    ruta = f"clinicas/{id_}"
    clinica = p.api.consultar(ruta)
    p.titulo.value = clinica["nombre"]
    p.agregar(p.enlace("Volver a clínicas", "/clinicas"))
    if p.api.sesion.rol == "ADMIN":
        confirmar = ft.Checkbox(label="Confirmar la baja de esta clínica")

        def baja() -> None:
            if not confirmar.value:
                from frontend.api import ErrorApi
                raise ErrorApi("Confirmá la baja de la clínica.")
            p.api.pedir("DELETE", ruta)
            p.ir("/clinicas")

        p.agregar(fila(confirmar, p.boton("Dar de baja", baja)))
        matricula, nombre = campo("Matrícula"), campo("Nombre del veterinario")
        usuario, clave = campo("Usuario de acceso (opcional)"), campo("Contraseña (opcional)", password=True)

        def alta() -> None:
            datos = {"nombre": nombre.value, "matricula": matricula.value}
            if usuario.value or clave.value:
                datos["acceso"] = {"nombre_usuario": usuario.value or "", "contrasena": clave.value or ""}
            p.guardar(f"{ruta}/veterinarios", datos)

        p.agregar(seccion("Nuevo veterinario", fila(matricula, nombre, usuario, clave),
                          p.boton("Agregar veterinario", alta)))
    p.agregar(seccion("Veterinarios", tabla(p.api.consultar(f"{ruta}/veterinarios"),
                                            ["id", "matricula", "nombre", "activo"])))
    p.agregar(seccion("Consultas", tabla(p.api.consultar("consultas", clinica_id=id_),
        ["numero", "fecha", "veterinario_id", "mascota_id", "complejidad", "costo"],
        lambda c: p.enlace("Ver consulta", f"/consultas/{c['id']}"))))
    if p.api.sesion.rol == "ADMIN":
        p.agregar(panel_reporte(p, id_))
