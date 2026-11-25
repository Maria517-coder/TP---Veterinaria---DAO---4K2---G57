/* R7: Reportes - 5 reportes con filtros, filas/totales. */
import { api } from "../api.js";
import { cargarCatalogos, obtenerEstado } from "../estado.js";
import {
  agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, limpiar,
  mensaje, selectOpciones, tabla, textoOVacio,
} from "../ui.js";

const REPORTES = [
  { id: "facturacion", titulo: "Facturación desglosada", ruta: "/reportes/facturacion", usaFechas: true },
  { id: "atenciones", titulo: "Atenciones y derivaciones", ruta: "/reportes/atenciones-derivaciones", usaFechas: true },
  { id: "rechazadas", titulo: "Muestras rechazadas", ruta: "/reportes/muestras-rechazadas", usaFechas: true },
  { id: "vacunas", titulo: "Vacunas pendientes", ruta: "/reportes/vacunas-pendientes", usaFechas: false },
  { id: "tiempos", titulo: "Tiempos promedio", ruta: "/reportes/tiempos-promedio", usaFechas: true },
];

export async function montarReportes() {
  const app = document.getElementById("app");
  limpiar(app);

  const intro = crearElemento("section", "", "bloque-intro");
  intro.appendChild(crearElemento("h2", "Reportes"));
  intro.appendChild(crearElemento("p", "Consultá los 5 reportes con filtros opcionales. Cada reporte muestra filas y totales.", "texto-secundario"));
  app.appendChild(intro);

  await cargarCatalogos();
  const { clinicas } = obtenerEstado();

  const tarjeta = crearTarjeta("Generar reporte");
  const selReporte = selectOpciones(REPORTES, { placeholder: "Seleccionar reporte…", valor: "id", texto: "titulo" });
  selReporte.id = "reporte-tipo";
  const selClinica = selectOpciones(clinicas, { placeholder: "Todas las clínicas…" });
  selClinica.id = "reporte-clinica";
  const desde = entradaTexto("", "date"); desde.id = "reporte-desde";
  const hasta = entradaTexto("", "date"); hasta.id = "reporte-hasta";

  const filtros = crearElemento("div", "", "grilla-3");
  filtros.appendChild(campo("Reporte", selReporte, selReporte.id));
  filtros.appendChild(campo("Clínica (opcional)", selClinica, selClinica.id));
  filtros.appendChild(campo("Desde", desde, desde.id));
  filtros.appendChild(campo("Hasta", hasta, hasta.id));
  tarjeta.appendChild(filtros);

  const ayuda = crearElemento("p", "Las fechas aplican a los reportes que las usan. “Vacunas pendientes” no usa rango de fechas.", "texto-secundario");
  ayuda.style.marginBottom = "16px";
  tarjeta.appendChild(ayuda);

  const acciones = crearElemento("div", "", "bloque-acciones");
  const cont = crearElemento("div", "", "seccion");
  tarjeta.appendChild(acciones);
  tarjeta.appendChild(cont);
  app.appendChild(tarjeta);

  async function generar() {
    limpiar(cont);
    const def = REPORTES.find((r) => r.id === selReporte.value);
    if (!def) { mensaje(cont, "Seleccioná un reporte.", "error"); return; }
    try {
      const params = new URLSearchParams();
      if (selClinica.value) params.set("clinica_id", selClinica.value);
      if (def.usaFechas && desde.value) params.set("desde", desde.value);
      if (def.usaFechas && hasta.value) params.set("hasta", hasta.value);
      const q = params.toString();
      const reporte = await api(`${def.ruta}${q ? `?${q}` : ""}`);
      renderReporte(cont, reporte);
    } catch (e) { mensaje(cont, e.message, "error"); }
  }

  agregarBoton(acciones, "Generar reporte", generar);
}

function renderReporte(contenedor, reporte) {
  limpiar(contenedor);
  contenedor.appendChild(crearElemento("h3", reporte.titulo || "Reporte"));

  const filas = Array.isArray(reporte.filas) ? reporte.filas : [];
  if (!filas.length) {
    textoOVacio(contenedor, "No hay filas para los filtros seleccionados.");
  } else {
    const columnas = Object.keys(filas[0]);
    contenedor.appendChild(tabla(
      columnas.map(formatearColumna),
      filas.map((fila) => columnas.map((col) => formatearValor(fila[col]))),
    ));
  }

  const totales = reporte.totales && typeof reporte.totales === "object" ? reporte.totales : {};
  const entradas = Object.entries(totales);
  if (entradas.length) {
    contenedor.appendChild(crearElemento("h4", "Totales"));
    const grid = crearElemento("div", "", "resumen-grid");
    entradas.forEach(([clave, valor]) => {
      const item = crearElemento("div", "", "resumen-item");
      item.appendChild(crearElemento("div", formatearColumna(clave), "etiqueta"));
      item.appendChild(crearElemento("div", String(valor), "valor"));
      grid.appendChild(item);
    });
    contenedor.appendChild(grid);
  }
}

function formatearColumna(clave) {
  return String(clave)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function formatearValor(valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  if (typeof valor === "object") return JSON.stringify(valor);
  return String(valor);
}
