/* R6: Laboratorio y envíos - muestras, contenedores, remitos y flujo completo. */
import { api, descargarPdf } from "../api.js";
import { cargarCatalogos, obtenerEstado } from "../estado.js";
import {
  agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, etiquetaEstado,
  etiquetaEstadoRemito, formatearFechaHora, limpiar, llenarSelect, mensaje, pestanas,
  selectOpciones, tabla, textoOVacio, vinculo,
} from "../ui.js";

const ESTADOS_MUESTRA = ["Extraida", "Empaquetada", "EnTransito", "Recibida", "Analizada", "Rechazada"];

export async function montarLaboratorio() {
  const app = document.getElementById("app");
  limpiar(app);
  const intro = crearElemento("section", "", "bloque-intro");
  intro.appendChild(crearElemento("h2", "Laboratorio y envíos"));
  intro.appendChild(crearElemento("p", "Seguí muestras por estado, armá contenedores, generá remitos y registrá el flujo completo.", "texto-secundario"));
  app.appendChild(intro);
  const mensajes = crearElemento("div");
  app.appendChild(mensajes);

  await cargarCatalogos();
  const tarjeta = crearTarjeta();
  tarjeta.appendChild(pestanas([
    { id: "muestras", titulo: "Muestras", render: (p) => tabMuestras(p) },
    { id: "contenedores", titulo: "Contenedores", render: (p) => tabContenedores(p, mensajes) },
    { id: "remitos", titulo: "Remitos", render: (p) => tabRemitos(p) },
  ], "muestras"));
  app.appendChild(tarjeta);
}

async function tabMuestras(panel) {
  limpiar(panel);
  const { clinicas } = obtenerEstado();
  const filtros = crearElemento("div", "", "grilla-3");
  const selEstado = selectOpciones(ESTADOS_MUESTRA.map((e) => ({ id: e, nombre: e })), { placeholder: "Todos los estados…" });
  selEstado.id = "m-filtro-estado";
  const selClinica = selectOpciones(clinicas, { placeholder: "Todas las clínicas…" });
  selClinica.id = "m-filtro-clinica";
  const fecha = entradaTexto("", "date"); fecha.id = "m-filtro-fecha";
  filtros.appendChild(campo("Estado", selEstado, selEstado.id));
  filtros.appendChild(campo("Clínica", selClinica, selClinica.id));
  filtros.appendChild(campo("Fecha", fecha, fecha.id));
  panel.appendChild(filtros);
  const acciones = crearElemento("div", "", "bloque-acciones");
  const cont = crearElemento("div", "", "seccion");
  panel.appendChild(acciones);
  panel.appendChild(cont);

  async function cargar() {
    limpiar(cont);
    cont.appendChild(crearElemento("p", "Cargando muestras…", "texto-secundario"));
    try {
      const params = new URLSearchParams();
      if (selEstado.value) params.set("estado", selEstado.value);
      if (selClinica.value) params.set("clinica_id", selClinica.value);
      if (fecha.value) params.set("fecha", fecha.value);
      const q = params.toString();
      const muestras = await api(`/muestras${q ? `?${q}` : ""}`);
      limpiar(cont);
      if (!muestras.length) { textoOVacio(cont, "No hay muestras para los filtros seleccionados."); return; }
      cont.appendChild(tabla(
        ["Id", "Consulta", "Tipo", "Estado", "Fecha", "Contenedor", "Ficha"],
        muestras.map((m) => [
          m.id, m.consulta_id, m.tipo_muestra_id, etiquetaEstado(m.estado), m.fecha,
          m.contenedor_id ?? "—", vinculo("Ver", `#/muestras/${m.id}`),
        ]),
      ));
    } catch (e) { limpiar(cont); mensaje(cont, e.message, "error"); }
  }

  agregarBoton(acciones, "Buscar muestras", cargar);
  await cargar();
}

async function tabContenedores(panel, mensajesGlobal) {
  limpiar(panel);
  const acciones = crearElemento("div", "", "bloque-acciones");
  agregarBoton(acciones, "Crear contenedor", async () => {
    try {
      const c = await api("/contenedores", { method: "POST", body: {} });
      mensaje(mensajesGlobal, `Contenedor ${c.numero} creado.`, "ok");
      await cargar();
    } catch (e) { mensaje(mensajesGlobal, e.message, "error"); }
  });
  panel.appendChild(acciones);
  const cont = crearElemento("div", "", "seccion");
  panel.appendChild(cont);

  async function cargar() {
    limpiar(cont);
    try {
      const contenedores = await api("/contenedores");
      if (!contenedores.length) { textoOVacio(cont, "No hay contenedores."); return; }
      cont.appendChild(tabla(
        ["Id", "Número", "Precinto", "Muestras", "Remito", "Ficha"],
        contenedores.map((c) => [
          c.id, c.numero, c.precinto_intacto ? "Intacto" : "Roto", c.cantidad_muestras,
          c.remito_id ?? "Sin remito", vinculo("Ver", `#/contenedores/${c.id}`),
        ]),
      ));
    } catch (e) { mensaje(cont, e.message, "error"); }
  }
  await cargar();
}

async function tabRemitos(panel) {
  limpiar(panel);
  const filtros = crearElemento("div", "", "grilla-3");
  const selEstado = selectOpciones(["GENERADO", "DESPACHADO", "RECIBIDO", "CERRADO"].map((e) => ({ id: e, nombre: e })), { placeholder: "Todos los estados…" });
  selEstado.id = "r-filtro-estado";
  const desde = entradaTexto("", "date"); desde.id = "r-filtro-desde";
  const hasta = entradaTexto("", "date"); hasta.id = "r-filtro-hasta";
  filtros.appendChild(campo("Estado", selEstado, selEstado.id));
  filtros.appendChild(campo("Desde", desde, desde.id));
  filtros.appendChild(campo("Hasta", hasta, hasta.id));
  panel.appendChild(filtros);
  const acciones = crearElemento("div", "", "bloque-acciones");
  const cont = crearElemento("div", "", "seccion");
  panel.appendChild(acciones);
  panel.appendChild(cont);

  async function cargar() {
    limpiar(cont);
    try {
      const params = new URLSearchParams();
      if (selEstado.value) params.set("estado", selEstado.value);
      if (desde.value) params.set("desde", desde.value);
      if (hasta.value) params.set("hasta", hasta.value);
      const q = params.toString();
      const remitos = await api(`/remitos${q ? `?${q}` : ""}`);
      if (!remitos.length) { textoOVacio(cont, "No hay remitos para los filtros seleccionados."); return; }
      cont.appendChild(tabla(
        ["Id", "Número", "Estado", "Destino", "Emisión", "Ficha"],
        remitos.map((r) => [r.id, r.numero, etiquetaEstadoRemito(r.estado), r.laboratorio_destino, formatearFechaHora(r.fecha_emision), vinculo("Ver", `#/remitos/${r.id}`)]),
      ));
    } catch (e) { mensaje(cont, e.message, "error"); }
  }
  agregarBoton(acciones, "Buscar remitos", cargar);
  await cargar();
}

export async function montarContenedorDetalle({ params }) {
  const app = document.getElementById("app");
  limpiar(app);
  const id = Number(params.id);
  const mensajes = crearElemento("div");
  try {
    const contenedor = await api(`/contenedores/${id}`);
    app.appendChild(vinculo("← Volver a Laboratorio y envíos", "#/laboratorio"));
    const intro = crearElemento("section", "", "bloque-intro");
    intro.appendChild(crearElemento("h2", `Contenedor ${contenedor.numero}`));
    intro.appendChild(crearElemento("p", `ID ${contenedor.id} · Precinto ${contenedor.precinto_intacto ? "intacto" : "roto"}`, "texto-secundario"));
    app.appendChild(intro);
    app.appendChild(mensajes);

    const tarjeta = crearTarjeta("Detalle del contenedor");
    const dl = crearElemento("dl", "", "lista-datos");
    [["ID", contenedor.id], ["Número", contenedor.numero], ["Precinto intacto", contenedor.precinto_intacto ? "Sí" : "No"], ["Cantidad muestras", contenedor.cantidad_muestras], ["Remito", contenedor.remito_id ?? "Sin remito"]].forEach(([k, v]) => {
      dl.appendChild(crearElemento("dt", k)); dl.appendChild(crearElemento("dd", String(v)));
    });
    tarjeta.appendChild(dl);
    const acciones = crearElemento("div", "", "bloque-acciones");
    if (contenedor.precinto_intacto) {
      agregarBoton(acciones, "Romper precinto", async () => {
        try {
          await api(`/contenedores/${id}/romper-precinto`, { method: "POST" });
          mensaje(mensajes, "Precinto marcado como roto.", "ok");
          await montarContenedorDetalle({ params });
        } catch (e) { mensaje(mensajes, e.message, "error"); }
      }, "boton boton-peligro");
    }
    if (contenedor.remito_id) {
      acciones.appendChild(vinculo("Ver remito", `#/remitos/${contenedor.remito_id}`, "boton boton-secundario"));
    }
    tarjeta.appendChild(acciones);
    app.appendChild(tarjeta);

    const tMuestras = crearTarjeta("Muestras del contenedor");
    try {
      const muestras = await api(`/muestras?contenedor_id=${id}`);
      if (!muestras.length) textoOVacio(tMuestras, "Este contenedor no tiene muestras.");
      else tMuestras.appendChild(tabla(["Id", "Tipo", "Estado", "Fecha", "Ficha"], muestras.map((m) => [m.id, m.tipo_muestra_id, etiquetaEstado(m.estado), m.fecha, vinculo("Ver", `#/muestras/${m.id}`)])));
    } catch (e) { mensaje(tMuestras, e.message, "error"); }
    app.appendChild(tMuestras);

    if (!contenedor.remito_id) {
      app.appendChild(formAgregarMuestra(id, mensajes));
      app.appendChild(formGenerarRemito(id, mensajes));
    }
  } catch (error) { mensaje(app, error.message, "error"); }
}

function formAgregarMuestra(contenedorId, mensajes) {
  const tarjeta = crearTarjeta("Agregar muestra al contenedor");
  tarjeta.appendChild(crearElemento("p", "Solo se pueden agregar muestras en estado Extraída, sin contenedor y de la misma clínica.", "texto-secundario"));
  const sel = document.createElement("select"); sel.id = `add-muestra-${contenedorId}`;
  const responsable = entradaTexto("Responsable"); responsable.id = `add-resp-${contenedorId}`;
  const fila = crearElemento("div", "", "grilla-2");
  fila.appendChild(campo("Muestra (Extraída, sin contenedor)", sel, sel.id));
  fila.appendChild(campo("Responsable", responsable, responsable.id));
  tarjeta.appendChild(fila);
  const acciones = crearElemento("div", "", "bloque-acciones");
  tarjeta.appendChild(acciones);

  async function cargarOpciones() {
    try {
      const extraidas = await api("/muestras?estado=Extraida");
      const candidatas = extraidas.filter((m) => !m.contenedor_id);
      llenarSelect(sel, candidatas, { placeholder: "Seleccionar muestra…", texto: (m) => `Muestra ${m.id} · consulta ${m.consulta_id} · tipo ${m.tipo_muestra_id}` });
    } catch (e) { mensaje(tarjeta, e.message, "error"); }
  }
  cargarOpciones();
  agregarBoton(acciones, "Agregar muestra", async () => {
    try {
      await api(`/contenedores/${contenedorId}/muestras`, { method: "POST", body: { muestra_id: Number(sel.value), responsable: responsable.value } });
      mensaje(mensajes, "Muestra agregada al contenedor.", "ok");
      await montarContenedorDetalle({ params: { id: String(contenedorId) } });
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });
  return tarjeta;
}

function formGenerarRemito(contenedorId, mensajes) {
  const tarjeta = crearTarjeta("Generar remito");
  const destino = entradaTexto("Laboratorio Central"); destino.id = `remito-dest-${contenedorId}`;
  tarjeta.appendChild(campo("Laboratorio destino", destino, destino.id));
  agregarBoton(tarjeta, "Generar remito", async () => {
    try {
      const remito = await api(`/contenedores/${contenedorId}/remito`, { method: "POST", body: { laboratorio_destino: destino.value } });
      mensaje(mensajes, `Remito ${remito.numero} generado.`, "ok");
      window.location.hash = `#/remitos/${remito.id}`;
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });
  return tarjeta;
}

export async function montarRemitoDetalle({ params }) {
  const app = document.getElementById("app");
  limpiar(app);
  const id = Number(params.id);
  const mensajes = crearElemento("div");
  try {
    const remito = await api(`/remitos/${id}`);
    app.appendChild(vinculo("← Volver a Laboratorio y envíos", "#/laboratorio"));
    const intro = crearElemento("section", "", "bloque-intro");
    intro.appendChild(crearElemento("h2", `Remito ${remito.numero}`));
    intro.appendChild(crearElemento("p", `Estado: ${remito.estado} · Destino: ${remito.laboratorio_destino}`, "texto-secundario"));
    app.appendChild(intro);
    app.appendChild(mensajes);

    const tarjeta = crearTarjeta("Detalle del remito");
    const dl = crearElemento("dl", "", "lista-datos");
    const clinicaOrigen = crearElemento("dd", String(remito.clinica_origen_id));
    [["ID", remito.id], ["Número", remito.numero], ["Estado", remito.estado], ["Destino", remito.laboratorio_destino], ["Clínica origen", remito.clinica_origen_id], ["Contenedor", remito.contenedor_id], ["Emisión", formatearFechaHora(remito.fecha_emision)], ["Despacho", formatearFechaHora(remito.fecha_hora_despacho)], ["Recepción", formatearFechaHora(remito.fecha_hora_recepcion)]].forEach(([k, v]) => {
      dl.appendChild(crearElemento("dt", k));
      dl.appendChild(k === "Clínica origen" ? clinicaOrigen : crearElemento("dd", String(v ?? "—")));
    });
    tarjeta.appendChild(dl);

    const responsable = entradaTexto("Responsable"); responsable.id = `remito-resp-${id}`;
    tarjeta.appendChild(campo("Responsable de la acción", responsable, responsable.id));
    const acciones = crearElemento("div", "", "bloque-acciones");
    if (remito.estado === "GENERADO") {
      agregarBoton(acciones, "Despachar remito", async () => {
        try {
          await api(`/remitos/${id}/despachar`, { method: "POST", body: { responsable: responsable.value } });
          mensaje(mensajes, "Remito despachado.", "ok");
          await montarRemitoDetalle({ params });
        } catch (e) { mensaje(mensajes, e.message, "error"); }
      });
    }
    if (remito.estado === "DESPACHADO") {
      agregarBoton(acciones, "Registrar recepción", async () => {
        try {
          await api(`/remitos/${id}/recepcion`, { method: "POST", body: { responsable: responsable.value } });
          mensaje(mensajes, "Recepción registrada.", "ok");
          await montarRemitoDetalle({ params });
        } catch (e) { mensaje(mensajes, e.message, "error"); }
      });
    }
    agregarBoton(acciones, "Descargar PDF", async () => {
      try { await descargarPdf(`/remitos/${id}/imprimir`, `remito-${id}.pdf`); }
      catch (e) { mensaje(mensajes, e.message, "error"); }
    }, "boton boton-secundario");
    agregarBoton(acciones, "Ver tiempo de tránsito", async () => {
      try {
        const r = await api(`/remitos/${id}/tiempo-transito`);
        mensaje(mensajes, `Tiempo de tránsito: ${r.tiempo_transito} segundos.`, "info");
      } catch (e) { mensaje(mensajes, e.message, "error"); }
    }, "boton boton-secundario");
    tarjeta.appendChild(acciones);
    app.appendChild(tarjeta);

    const tMuestras = crearTarjeta("Muestras del remito");
    try {
      const muestras = await api(`/muestras?contenedor_id=${remito.contenedor_id}`);
      if (!muestras.length) textoOVacio(tMuestras, "No hay muestras asociadas a este remito.");
      else tMuestras.appendChild(tabla(["Id", "Tipo", "Estado", "Fecha", "Ficha"], muestras.map((m) => [m.id, m.tipo_muestra_id, etiquetaEstado(m.estado), m.fecha, vinculo("Ver", `#/muestras/${m.id}`)])));
    } catch (e) { mensaje(tMuestras, e.message, "error"); }
    app.appendChild(tMuestras);

    try {
      const clinicas = await api("/clinicas");
      const clinica = clinicas.find((c) => c.id === remito.clinica_origen_id);
      if (clinica) clinicaOrigen.textContent = `${remito.clinica_origen_id} (${clinica.nombre})`;
    } catch {
      // El detalle ya muestra el ID aunque el catálogo no esté disponible.
    }
  } catch (error) { mensaje(app, error.message, "error"); }
}

export async function montarMuestraDetalle({ params }) {
  const app = document.getElementById("app");
  limpiar(app);
  const id = Number(params.id);
  const mensajes = crearElemento("div");
  try {
    const [muestra, historial] = await Promise.all([
      api(`/muestras/${id}`),
      api(`/muestras/${id}/historial-estados`),
    ]);
    app.appendChild(vinculo("← Volver a Laboratorio y envíos", "#/laboratorio"));
    const intro = crearElemento("section", "", "bloque-intro");
    intro.appendChild(crearElemento("h2", `Muestra ${muestra.id}`));
    intro.appendChild(crearElemento("p", `Estado actual: ${muestra.estado}`, "texto-secundario"));
    app.appendChild(intro);
    app.appendChild(mensajes);

    const tarjeta = crearTarjeta("Detalle de la muestra");
    const dl = crearElemento("dl", "", "lista-datos");
    [["ID", muestra.id], ["Consulta", muestra.consulta_id], ["Tipo de muestra", muestra.tipo_muestra_id], ["Contenedor", muestra.contenedor_id ?? "—"], ["Estado", muestra.estado], ["Fecha", muestra.fecha], ["Resultado", muestra.resultado ?? "—"], ["Fecha resultado", muestra.fecha_resultado ?? "—"]].forEach(([k, v]) => {
      dl.appendChild(crearElemento("dt", k)); dl.appendChild(crearElemento("dd", String(v)));
    });
    tarjeta.appendChild(dl);
    app.appendChild(tarjeta);

    if (muestra.estado === "Recibida") {
      const tRes = crearTarjeta("Registrar resultado");
      const texto = document.createElement("textarea"); texto.id = `res-texto-${id}`; texto.placeholder = "Texto del resultado";
      const responsable = entradaTexto("Responsable"); responsable.id = `res-resp-${id}`;
      tRes.appendChild(campo("Resultado", texto, texto.id));
      tRes.appendChild(campo("Responsable", responsable, responsable.id));
      agregarBoton(tRes, "Registrar resultado", async () => {
        try {
          await api(`/muestras/${id}/resultado`, { method: "POST", body: { texto: texto.value, responsable: responsable.value } });
          mensaje(mensajes, "Resultado registrado. La muestra pasó a Analizada.", "ok");
          await montarMuestraDetalle({ params });
        } catch (e) { mensaje(mensajes, e.message, "error"); }
      });
      app.appendChild(tRes);
    }

    const tHist = crearTarjeta("Historial de estados");
    if (!historial.length) textoOVacio(tHist, "Sin historial de estados.");
    else tHist.appendChild(tabla(["Id", "Estado", "Fecha y hora", "Responsable"], historial.map((h) => [h.id, etiquetaEstado(h.estado), formatearFechaHora(h.fecha_hora), h.responsable])));
    app.appendChild(tHist);
  } catch (error) { mensaje(app, error.message, "error"); }
}
