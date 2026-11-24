/* R2: Red y clínicas - lista y ficha con tabs. */
import { api, esAdmin } from "../api.js";
import { cargarCatalogos, obtenerEstado } from "../estado.js";
import {
  agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, etiquetaEstadoRemito,
  formatearFechaHora, limpiar, llenarSelect, mensaje, pestanas, tabla, textoOVacio, vinculo,
} from "../ui.js";

export async function montarClinicas() {
  const app = document.getElementById("app");
  limpiar(app);

  const titulo = crearElemento("section", "", "bloque-intro");
  titulo.appendChild(crearElemento("h2", "Red y clínicas"));
  titulo.appendChild(crearElemento("p", "Administrá las clínicas de la red y entrá a la ficha para ver veterinarios, consultas y facturación.", "texto-secundario"));
  app.appendChild(titulo);

  const mensajes = crearElemento("div");
  app.appendChild(mensajes);

  if (esAdmin()) {
    const formTarjeta = crearTarjeta("Nueva clínica");
    const nombre = entradaTexto("Nombre de la clínica");
    nombre.id = "clinica-nombre";
    formTarjeta.appendChild(campo("Nombre", nombre, "clinica-nombre"));
    agregarBoton(formTarjeta, "Crear clínica", async () => {
      try {
        await api("/red/clinicas", { method: "POST", body: { nombre: nombre.value } });
        nombre.value = "";
        mensaje(mensajes, "Clínica creada correctamente.", "ok");
        await renderLista();
      } catch (error) {
        mensaje(mensajes, error.message, "error");
      }
    });
    app.appendChild(formTarjeta);
  }

  const listaTarjeta = crearTarjeta("Clínicas registradas");
  const contLista = crearElemento("div");
  listaTarjeta.appendChild(contLista);
  app.appendChild(listaTarjeta);

  async function renderLista() {
    limpiar(contLista);
    try {
      await cargarCatalogos();
      const { clinicas } = obtenerEstado();
      if (clinicas.length === 0) {
        textoOVacio(contLista, "Todavía no hay clínicas registradas.");
        return;
      }
      contLista.appendChild(tabla(
        ["Id", "Nombre", "Ficha"],
        clinicas.map((c) => [c.id, c.nombre, vinculo("Ver ficha", `#/clinicas/${c.id}`)]),
      ));
    } catch (error) {
      mensaje(contLista, error.message, "error");
    }
  }

  await renderLista();
}

export async function montarClinicaDetalle({ params }) {
  const app = document.getElementById("app");
  limpiar(app);
  const id = Number(params.id);
  const mensajes = crearElemento("div");
  app.appendChild(mensajes);

  try {
    const clinica = await api(`/clinicas/${id}`);
    const cabecera = crearElemento("section", "", "bloque-intro");
    cabecera.appendChild(vinculo("? Volver a clínicas", "#/clinicas"));
    cabecera.appendChild(crearElemento("h2", `Clínica: ${clinica.nombre}`));
    cabecera.appendChild(crearElemento("p", `ID ${clinica.id} ? Red ${clinica.red_id}`, "texto-secundario"));
    if (esAdmin()) {
      const accionesCab = crearElemento("div", "", "bloque-acciones");
      agregarBoton(accionesCab, "Dar de baja", async () => {
        if (!window.confirm(`?Dar de baja la clínica "${clinica.nombre}"?`)) return;
        try {
          await api(`/clinicas/${clinica.id}`, { method: "DELETE" });
          window.location.hash = "#/clinicas";
        } catch (error) {
          mensaje(mensajes, error.message, "error");
        }
      }, "boton boton-peligro");
      cabecera.appendChild(accionesCab);
    }
    app.appendChild(cabecera);
    app.appendChild(mensajes);

    const tarjeta = crearTarjeta();
    tarjeta.appendChild(pestanas([
      { id: "vets", titulo: "Veterinarios", render: (p) => tabVeterinarios(p, clinica, mensajes) },
      { id: "consultas", titulo: "Consultas", render: (p) => tabConsultas(p, clinica) },
      { id: "facturacion", titulo: "Facturación", render: (p) => tabFacturacion(p, clinica) },
    ], "vets"));
    app.appendChild(tarjeta);
  } catch (error) {
    mensaje(app, error.message, "error");
  }
}

async function tabVeterinarios(panel, clinica, mensajesGlobal) {
  limpiar(panel);
  const localMsg = crearElemento("div");
  panel.appendChild(localMsg);

  if (esAdmin()) {
    const form = crearElemento("div", "", "seccion");
    form.appendChild(crearElemento("h3", "Agregar veterinario"));
    const fila = crearElemento("div", "", "fila");
    const matricula = entradaTexto("MP-1234"); matricula.id = `mat-${clinica.id}`;
    const nombre = entradaTexto("Dra. Ana Pérez"); nombre.id = `nom-vet-${clinica.id}`;
    fila.appendChild(campo("Matrícula", matricula, matricula.id));
    fila.appendChild(campo("Nombre", nombre, nombre.id));
    form.appendChild(fila);

    const filaAcceso = crearElemento("div", "", "fila");
    const usuarioVet = entradaTexto("Usuario (opcional)"); usuarioVet.id = `usr-vet-${clinica.id}`;
    const passVet = entradaTexto("Contraseña (opcional)", "password"); passVet.id = `pass-vet-${clinica.id}`;
    filaAcceso.appendChild(campo("Usuario de acceso (opcional)", usuarioVet, usuarioVet.id));
    filaAcceso.appendChild(campo("Contraseña de acceso (opcional)", passVet, passVet.id));
    form.appendChild(filaAcceso);

    const acciones = crearElemento("div", "", "bloque-acciones");
    agregarBoton(acciones, "Agregar veterinario", async () => {
      try {
        const body = { matricula: matricula.value, nombre: nombre.value };
        const usr = usuarioVet.value.trim();
        const pwd = passVet.value;
        if (usr || pwd) {
          body.acceso = { nombre_usuario: usr, contrasena: pwd };
        }
        await api(`/clinicas/${clinica.id}/veterinarios`, { method: "POST", body });
        matricula.value = ""; nombre.value = ""; usuarioVet.value = ""; passVet.value = "";
        mensaje(localMsg, "Veterinario agregado.", "ok");
        await listar();
      } catch (error) { mensaje(localMsg, error.message, "error"); }
    });
    form.appendChild(acciones);
    panel.appendChild(form);
  }

  const listado = crearElemento("div", "", "seccion");
  listado.appendChild(crearElemento("h3", "Veterinarios de la clínica"));
  const cont = crearElemento("div");
  listado.appendChild(cont);
  panel.appendChild(listado);

  async function listar() {
    limpiar(cont);
    try {
      const vets = await api(`/clinicas/${clinica.id}/veterinarios`);
      if (vets.length === 0) { textoOVacio(cont, "No hay veterinarios en esta clínica."); return; }
      cont.appendChild(tabla(
        ["Id", "Matrícula", "Nombre", "Activo"],
        vets.map((v) => [v.id, v.matricula, v.nombre, v.activo ? "Sí" : "No"]),
      ));
    } catch (error) { mensaje(cont, error.message, "error"); }
  }
  await listar();
}

async function tabConsultas(panel, clinica) {
  limpiar(panel);
  panel.appendChild(crearElemento("p", "Consultas registradas en esta clínica.", "texto-secundario"));
  try {
    const consultas = await api(`/consultas?clinica_id=${clinica.id}`);
    if (consultas.length === 0) { textoOVacio(panel, "No hay consultas para esta clínica."); return; }
    panel.appendChild(tabla(
      ["N°", "Fecha", "Veterinario", "Mascota", "Complejidad", "Costo", "Ficha"],
      consultas.map((c) => [
        c.numero, c.fecha, c.veterinario_id, c.mascota_id, c.complejidad, c.costo,
        vinculo("Ver", `#/consultas/${c.id}`),
      ]),
    ));
  } catch (error) { mensaje(panel, error.message, "error"); }
}

async function tabFacturacion(panel, clinica) {
  limpiar(panel);
  panel.appendChild(crearElemento("p", "Facturación desglosada para esta clínica.", "texto-secundario"));
  const filtros = crearElemento("div", "", "fila seccion");
  const desde = entradaTexto("", "date"); desde.id = `fac-desde-${clinica.id}`;
  const hasta = entradaTexto("", "date"); hasta.id = `fac-hasta-${clinica.id}`;
  filtros.appendChild(campo("Desde", desde, desde.id));
  filtros.appendChild(campo("Hasta", hasta, hasta.id));
  panel.appendChild(filtros);
  const acciones = crearElemento("div", "", "bloque-acciones");
  const resultado = crearElemento("div", "", "seccion");
  panel.appendChild(acciones);
  panel.appendChild(resultado);

  async function cargar() {
    limpiar(resultado);
    try {
      const params = new URLSearchParams({ clinica_id: String(clinica.id) });
      if (desde.value) params.set("desde", desde.value);
      if (hasta.value) params.set("hasta", hasta.value);
      const reporte = await api(`/reportes/facturacion?${params.toString()}`);
      resultado.appendChild(crearElemento("h3", reporte.titulo));
      if (!reporte.filas.length) { textoOVacio(resultado, "Sin datos para los filtros seleccionados."); }
      else {
        resultado.appendChild(tabla(
          ["Clínica", "Atenciones", "Análisis", "Total"],
          reporte.filas.map((f) => [f.clinica, f.atenciones, f.analisis, f.total]),
        ));
      }
      const totales = crearElemento("div", "", "resumen-grid");
      Object.entries(reporte.totales).forEach(([k, v]) => {
        const item = crearElemento("div", "", "resumen-item");
        item.appendChild(crearElemento("div", k, "etiqueta"));
        item.appendChild(crearElemento("div", String(v), "valor"));
        totales.appendChild(item);
      });
      resultado.appendChild(totales);
    } catch (error) { mensaje(resultado, error.message, "error"); }
  }

  agregarBoton(acciones, "Consultar facturación", cargar);
  await cargar();
}
