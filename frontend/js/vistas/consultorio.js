/* R4: Consultorio - registrar consulta, muestras, PDFs y ficha consulta. */
import { api, descargarPdf, esVeterinario, obtenerClinicaId, obtenerVeterinarioId } from "../api.js";
import { cargarCatalogos, cargarVeterinarios, obtenerEstado } from "../estado.js";
import {
  agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, etiquetaEstado,
  formatearFechaHora, limpiar, llenarSelect, mensaje, selectOpciones, tabla, textoOVacio, vinculo,
} from "../ui.js";

export async function montarConsultorio() {
  const app = document.getElementById("app");
  limpiar(app);
  const intro = crearElemento("section", "", "bloque-intro");
  intro.appendChild(crearElemento("h2", "Consultorio"));
  intro.appendChild(crearElemento("p", "Registr? la consulta paso a paso. Us? selectores, no IDs manuales.", "texto-secundario"));
  app.appendChild(intro);
  const mensajes = crearElemento("div");
  app.appendChild(mensajes);

  await cargarCatalogos();
  const { clinicas, tiposMuestra } = obtenerEstado();
  const clientes = await api("/clientes");

  const esVet = esVeterinario();
  const miVetId = obtenerVeterinarioId();

  const form = crearTarjeta("Nueva consulta");
  const selClinica = selectOpciones(clinicas, { placeholder: "Seleccionar clínica..." }); selClinica.id = "con-clinica";
  const selVet = selectOpciones([], { placeholder: "Seleccionar veterinario..." }); selVet.id = "con-vet";
  const selCliente = selectOpciones(clientes, { placeholder: "Seleccionar cliente...", texto: (c) => `${c.nombre} (${c.telefono})` }); selCliente.id = "con-cliente";
  const selMascota = selectOpciones([], { placeholder: "Seleccionar mascota..." }); selMascota.id = "con-mascota";
  const fecha = entradaTexto("", "date"); fecha.id = "con-fecha";
  const selComplejidad = selectOpciones([{ id: "BAJA", nombre: "BAJA" }, { id: "MEDIA", nombre: "MEDIA" }, { id: "ALTA", nombre: "ALTA" }], { placeholder: "Seleccionar complejidad...", valor: "id", texto: "nombre" }); selComplejidad.id = "con-complejidad";
  const costo = entradaTexto("100.00"); costo.id = "con-costo";

    if (esVet && miVetId) {
    try {
      let miClinicaId = obtenerClinicaId();
      if (!miClinicaId) {
        const yo = await api("/auth/yo");
        miClinicaId = yo.clinica_id ?? null;
      }
      if (miClinicaId) {
        selClinica.value = String(miClinicaId);
        selClinica.disabled = true;
        const vets = await cargarVeterinarios(miClinicaId);
        llenarSelect(selVet, vets, { placeholder: "Seleccionar veterinario...", texto: (v) => `${v.nombre} (${v.matricula})` });
        selVet.value = String(miVetId);
        selVet.disabled = true;
      }
    } catch (_e) { /* la protección real es del backend */ }
  }

  const g1 = crearElemento("div", "", "grilla-2");
  g1.appendChild(campo("Clínica", selClinica, selClinica.id));
  g1.appendChild(campo("Veterinario", selVet, selVet.id));
  g1.appendChild(campo("Cliente", selCliente, selCliente.id));
  g1.appendChild(campo("Mascota", selMascota, selMascota.id));
  g1.appendChild(campo("Fecha", fecha, fecha.id));
  g1.appendChild(campo("Complejidad", selComplejidad, selComplejidad.id));
  g1.appendChild(campo("Costo (texto, ej. 100.00)", costo, costo.id));
  form.appendChild(g1);

  const resultadoConsulta = crearElemento("div", "", "seccion");
  form.appendChild(crearElemento("div", "", "bloque-acciones"));
  const accionesForm = form.querySelector(".bloque-acciones");

  selClinica.addEventListener("change", async () => {
    llenarSelect(selVet, [], { placeholder: "Cargando veterinarios…" });
    try {
      const vets = await cargarVeterinarios(Number(selClinica.value));
      llenarSelect(selVet, vets, { placeholder: "Seleccionar veterinario…", texto: (v) => `${v.nombre} (${v.matricula})` });
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });
  selCliente.addEventListener("change", async () => {
    llenarSelect(selMascota, [], { placeholder: "Cargando mascotas…" });
    try {
      const mascotas = await api(`/clientes/${selCliente.value}/mascotas`);
      llenarSelect(selMascota, mascotas, { placeholder: "Seleccionar mascota…" });
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });

  let consultaActual = null;
  agregarBoton(accionesForm, "Registrar consulta", async () => {
    limpiar(resultadoConsulta);
    try {
      consultaActual = await api("/consultas", {
        method: "POST",
        body: {
          veterinario_id: Number(selVet.value),
          mascota_id: Number(selMascota.value),
          fecha: fecha.value,
          complejidad: selComplejidad.value,
          costo: costo.value,
        },
      });
      mensaje(mensajes, `Consulta ${consultaActual.numero} registrada.`, "ok");
      renderConsultaCreada(resultadoConsulta, consultaActual, tiposMuestra, mensajes);
    } catch (error) { mensaje(mensajes, error.message, "error"); }
  });
  form.appendChild(resultadoConsulta);
  app.appendChild(form);
}

function renderConsultaCreada(contenedor, consulta, tiposMuestra, mensajes) {
  limpiar(contenedor);
  contenedor.appendChild(crearElemento("h3", `Consulta registrada: ${consulta.numero}`));

  if (consulta.vacunas_pendientes && consulta.vacunas_pendientes.length) {
    const aviso = crearElemento("div", "", "aviso");
    aviso.appendChild(crearElemento("strong", "Aviso de vacunas pendientes: "));
    aviso.appendChild(document.createTextNode(consulta.vacunas_pendientes.map((v) => v.nombre).join(", ")));
    contenedor.appendChild(aviso);
  } else {
    const ok = crearElemento("p", "No hay vacunas obligatorias pendientes para esta mascota.", "mensaje mensaje-ok");
    contenedor.appendChild(ok);
  }

  const acciones = crearElemento("div", "", "bloque-acciones");
  agregarBoton(acciones, "Ver ficha de consulta", () => { window.location.hash = `#/consultas/${consulta.id}`; }, "boton boton-secundario");
  agregarBoton(acciones, "Descargar comprobante PDF", async () => {
    try { await descargarPdf(`/consultas/${consulta.id}/comprobante`, `comprobante-${consulta.id}.pdf`); }
    catch (e) { mensaje(mensajes, e.message, "error"); }
  }, "boton boton-secundario");
  contenedor.appendChild(acciones);

  const secMuestra = crearElemento("div", "", "seccion");
  secMuestra.appendChild(crearElemento("h3", "Agregar muestra a la consulta"));
  const fila = crearElemento("div", "", "fila");
  const selTipo = selectOpciones(tiposMuestra, { placeholder: "Seleccionar tipo de muestra…", texto: (t) => `${t.nombre} (${t.costo_analisis})` });
  selTipo.id = `tipo-muestra-${consulta.id}`;
  fila.appendChild(campo("Tipo de muestra", selTipo, selTipo.id));
  secMuestra.appendChild(fila);
  const listaMuestras = crearElemento("div", "", "seccion");
  const accionesM = crearElemento("div", "", "bloque-acciones");
  agregarBoton(accionesM, "Agregar muestra", async () => {
    try {
      await api(`/consultas/${consulta.id}/muestras`, { method: "POST", body: { tipo_muestra_id: Number(selTipo.value) } });
      mensaje(mensajes, "Muestra agregada.", "ok");
      await refrescarMuestras(consulta.id, listaMuestras, mensajes);
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });
  secMuestra.appendChild(accionesM);
  contenedor.appendChild(secMuestra);
  contenedor.appendChild(listaMuestras);

  const secCosto = crearElemento("div", "", "seccion");
  const contCosto = crearElemento("div");
  secCosto.appendChild(crearElemento("h3", "Costo total"));
  agregarBoton(secCosto, "Calcular costo total", async () => {
    try {
      const r = await api(`/consultas/${consulta.id}/costo-total`);
      limpiar(contCosto);
      const item = crearElemento("div", "", "resumen-grid");
      const card = crearElemento("div", "", "resumen-item");
      card.appendChild(crearElemento("div", "Costo total", "etiqueta"));
      card.appendChild(crearElemento("div", String(r.costo_total), "valor"));
      item.appendChild(card);
      contCosto.appendChild(item);
    } catch (e) { mensaje(contCosto, e.message, "error"); }
  }, "boton boton-secundario");
  secCosto.appendChild(contCosto);
  contenedor.appendChild(secCosto);

  const secPdf = crearElemento("div", "", "seccion");
  secPdf.appendChild(crearElemento("h3", "Documentos PDF"));
  const accPdf = crearElemento("div", "", "bloque-acciones");
  agregarBoton(accPdf, "Orden de derivación PDF", async () => {
    try { await descargarPdf(`/consultas/${consulta.id}/orden-derivacion`, `orden-derivacion-${consulta.id}.pdf`); }
    catch (e) { mensaje(mensajes, e.message, "error"); }
  }, "boton boton-secundario");
  agregarBoton(accPdf, "Comprobante PDF", async () => {
    try { await descargarPdf(`/consultas/${consulta.id}/comprobante`, `comprobante-${consulta.id}.pdf`); }
    catch (e) { mensaje(mensajes, e.message, "error"); }
  }, "boton boton-secundario");
  secPdf.appendChild(accPdf);
  contenedor.appendChild(secPdf);

  refrescarMuestras(consulta.id, listaMuestras, mensajes).catch(() => {});
}

async function refrescarMuestras(consultaId, contenedor, mensajes) {
  limpiar(contenedor);
  try {
    const muestras = await api(`/consultas/${consultaId}/muestras`);
    contenedor.appendChild(crearElemento("h4", "Muestras de la consulta"));
    if (!muestras.length) { textoOVacio(contenedor, "Todavía no hay muestras registradas."); return; }
    contenedor.appendChild(tabla(["Id", "Tipo", "Estado", "Fecha"], muestras.map((m) => [m.id, m.tipo_muestra_id, etiquetaEstado(m.estado), m.fecha])));
  } catch (e) { mensaje(contenedor, e.message, "error"); }
}

export async function montarConsultaDetalle({ params }) {
  const app = document.getElementById("app");
  limpiar(app);
  const id = Number(params.id);
  try {
    const [consulta, muestras, costo] = await Promise.all([
      api(`/consultas/${id}`),
      api(`/consultas/${id}/muestras`),
      api(`/consultas/${id}/costo-total`),
    ]);
    app.appendChild(vinculo("← Volver al consultorio", "#/consultorio"));
    const intro = crearElemento("section", "", "bloque-intro");
    intro.appendChild(crearElemento("h2", `Consulta ${consulta.numero}`));
    intro.appendChild(crearElemento("p", `Fecha ${consulta.fecha} · Complejidad ${consulta.complejidad}`, "texto-secundario"));
    app.appendChild(intro);

    const tarjeta = crearTarjeta("Detalle de la consulta");
    const dl = crearElemento("dl", "", "lista-datos");
    [["N°", consulta.numero], ["Clínica", consulta.clinica_id], ["Veterinario", consulta.veterinario_id], ["Mascota", consulta.mascota_id], ["Fecha", consulta.fecha], ["Complejidad", consulta.complejidad], ["Costo", consulta.costo], ["Costo total", costo.costo_total]].forEach(([k, v]) => {
      dl.appendChild(crearElemento("dt", k)); dl.appendChild(crearElemento("dd", String(v)));
    });
    tarjeta.appendChild(dl);

    if (consulta.vacunas_pendientes && consulta.vacunas_pendientes.length) {
      const aviso = crearElemento("div", "", "aviso");
      aviso.appendChild(crearElemento("strong", "Vacunas pendientes: "));
      aviso.appendChild(document.createTextNode(consulta.vacunas_pendientes.map((v) => v.nombre).join(", ")));
      tarjeta.appendChild(aviso);
    }

    const acciones = crearElemento("div", "", "bloque-acciones");
    agregarBoton(acciones, "Orden de derivación PDF", async () => {
      try { await descargarPdf(`/consultas/${id}/orden-derivacion`, `orden-derivacion-${id}.pdf`); }
      catch (e) { mensaje(tarjeta, e.message, "error"); }
    }, "boton boton-secundario");
    agregarBoton(acciones, "Comprobante PDF", async () => {
      try { await descargarPdf(`/consultas/${id}/comprobante`, `comprobante-${id}.pdf`); }
      catch (e) { mensaje(tarjeta, e.message, "error"); }
    }, "boton boton-secundario");
    tarjeta.appendChild(acciones);
    app.appendChild(tarjeta);

    const tm = crearTarjeta("Muestras");
    if (!muestras.length) textoOVacio(tm, "Esta consulta no tiene muestras.");
    else tm.appendChild(tabla(["Id", "Tipo", "Estado", "Fecha", "Ficha"], muestras.map((m) => [m.id, m.tipo_muestra_id, etiquetaEstado(m.estado), m.fecha, vinculo("Ver", `#/muestras/${m.id}`)])));
    app.appendChild(tm);
  } catch (error) { mensaje(app, error.message, "error"); }
}
