/* R3: Recepción - clientes, mascotas, ficha mascota, vacunas. */
import { api, descargarPdf } from "../api.js";
import { ESPECIES, cargarCatalogos, cargarTodosVeterinarios, obtenerEstado } from "../estado.js";
import {
  agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, formatearFechaHora,
  limpiar, llenarSelect, mensaje, pestanas, selectOpciones, tabla, textoOVacio, vinculo,
} from "../ui.js";

export async function montarRecepcion() {
  const app = document.getElementById("app");
  limpiar(app);
  app.appendChild(crearElemento("section", "", "bloque-intro")).appendChild(crearElemento("h2", "Recepción"));
  app.querySelector(".bloque-intro").appendChild(crearElemento("p", "Buscá clientes y mascotas, registrá altas y cargá vacunas al catálogo.", "texto-secundario"));
  const mensajes = crearElemento("div");
  app.appendChild(mensajes);

  const grilla = crearElemento("div", "", "grilla-2");
  grilla.appendChild(formCliente(mensajes, () => Promise.all([listarClientes(), listarMascotas()])));
  const tarjetaMascota = formMascota(mensajes, () => listarMascotas());
  grilla.appendChild(tarjetaMascota);
  app.appendChild(grilla);
  app.appendChild(formVacuna(mensajes));

  const tarjetaClientes = crearTarjeta("Clientes");
  const contClientes = crearElemento("div");
  tarjetaClientes.appendChild(contClientes);
  app.appendChild(tarjetaClientes);

  const tarjetaMascotas = crearTarjeta("Mascotas");
  const buscador = entradaTexto("Buscar por nombre de mascota o cliente…");
  buscador.id = "buscar-mascota";
  tarjetaMascotas.appendChild(campo("Buscar", buscador, buscador.id));
  const contMascotas = crearElemento("div");
  tarjetaMascotas.appendChild(contMascotas);
  app.appendChild(tarjetaMascotas);

  let mascotasCache = [];
  let clientesCache = [];

  async function listarClientes() {
    limpiar(contClientes);
    try {
      clientesCache = await api("/clientes");
      if (!clientesCache.length) { textoOVacio(contClientes, "No hay clientes registrados."); return; }
      contClientes.appendChild(tabla(["Id", "Nombre", "Teléfono"], clientesCache.map((c) => [c.id, c.nombre, c.telefono])));
      refrescarSelectClientes();
    } catch (error) { mensaje(contClientes, error.message, "error"); }
  }

  function renderMascotas() {
    limpiar(contMascotas);
    const q = buscador.value.trim().toLowerCase();
    const filtradas = mascotasCache.filter((m) => {
      const cliente = clientesCache.find((c) => c.id === m.cliente_id);
      const nombreCliente = cliente ? cliente.nombre.toLowerCase() : "";
      return m.nombre.toLowerCase().includes(q) || nombreCliente.includes(q);
    });
    if (!filtradas.length) { textoOVacio(contMascotas, "No hay mascotas que coincidan con la búsqueda."); return; }
    contMascotas.appendChild(tabla(
      ["Id", "Nombre", "Cliente", "Especie", "Ficha"],
      filtradas.map((m) => {
        const cliente = clientesCache.find((c) => c.id === m.cliente_id);
        const esp = ESPECIES.find((e) => e.id === m.especie_id);
        return [m.id, m.nombre, cliente ? cliente.nombre : m.cliente_id, esp ? esp.nombre : m.especie_id, vinculo("Ver ficha", `#/mascotas/${m.id}`)];
      }),
    ));
  }

  async function listarMascotas() {
    try {
      mascotasCache = await api("/mascotas");
      renderMascotas();
    } catch (error) { mensaje(contMascotas, error.message, "error"); }
  }

  buscador.addEventListener("input", renderMascotas);
  const selectClienteMascota = tarjetaMascota._selectCliente;
  function refrescarSelectClientes() {
    llenarSelect(selectClienteMascota, clientesCache, { placeholder: "Seleccionar cliente…" , texto: (c) => `${c.nombre} (${c.telefono})` });
  }

  await cargarCatalogos();
  await listarClientes();
  await listarMascotas();
}

function formCliente(mensajes, alCrear) {
  const tarjeta = crearTarjeta("Nuevo cliente");
  const nombre = entradaTexto("Nombre y apellido"); nombre.id = "cliente-nombre";
  const telefono = entradaTexto("Teléfono"); telefono.id = "cliente-telefono";
  tarjeta.appendChild(campo("Nombre", nombre, nombre.id));
  tarjeta.appendChild(campo("Teléfono", telefono, telefono.id));
  agregarBoton(tarjeta, "Crear cliente", async () => {
    try {
      await api("/clientes", { method: "POST", body: { nombre: nombre.value, telefono: telefono.value } });
      nombre.value = ""; telefono.value = "";
      mensaje(mensajes, "Cliente creado.", "ok");
      await alCrear();
    } catch (error) { mensaje(mensajes, error.message, "error"); }
  });
  return tarjeta;
}

function formMascota(mensajes, alCrear) {
  const tarjeta = crearTarjeta("Nueva mascota");
  const selectCliente = document.createElement("select"); selectCliente.id = "mascota-cliente";
  const selectEspecie = selectOpciones(ESPECIES, { placeholder: "Seleccionar especie…" }); selectEspecie.id = "mascota-especie";
  const nombre = entradaTexto("Nombre de la mascota"); nombre.id = "mascota-nombre";
  const fecha = entradaTexto("", "date"); fecha.id = "mascota-fecha";
  tarjeta.appendChild(campo("Cliente responsable", selectCliente, selectCliente.id));
  tarjeta.appendChild(campo("Especie", selectEspecie, selectEspecie.id));
  tarjeta.appendChild(campo("Nombre", nombre, nombre.id));
  tarjeta.appendChild(campo("Fecha de nacimiento", fecha, fecha.id));
  agregarBoton(tarjeta, "Crear mascota", async () => {
    try {
      await api("/mascotas", {
        method: "POST",
        body: {
          cliente_id: Number(selectCliente.value),
          especie_id: Number(selectEspecie.value),
          nombre: nombre.value,
          fecha_nacimiento: fecha.value,
        },
      });
      nombre.value = ""; fecha.value = ""; selectEspecie.value = "";
      mensaje(mensajes, "Mascota creada. Su historia clínica fue creada automáticamente.", "ok");
      await alCrear();
    } catch (error) { mensaje(mensajes, error.message, "error"); }
  });
  tarjeta._selectCliente = selectCliente;
  return tarjeta;
}

function formVacuna(mensajes) {
  const tarjeta = crearTarjeta("Cargar vacuna");
  tarjeta.appendChild(crearElemento("p", "Cargá vacunas al catálogo para usarlas en consultas y vacunaciones.", "texto-secundario"));
  const nombre = entradaTexto("Nombre de la vacuna"); nombre.id = "vacuna-nombre";
  const obligatoria = document.createElement("input"); obligatoria.type = "checkbox"; obligatoria.id = "vacuna-obligatoria";
  const labelOb = crearElemento("label", "", "fila");
  labelOb.style.alignItems = "center"; labelOb.style.gap = "8px"; labelOb.style.marginBottom = "16px";
  labelOb.appendChild(obligatoria);
  labelOb.appendChild(crearElemento("span", "Es obligatoria"));
  const especiesCont = crearElemento("div", "", "fila");
  especiesCont.style.marginBottom = "16px";
  const checks = ESPECIES.map((e) => {
    const l = crearElemento("label", "", "fila");
    l.style.alignItems = "center"; l.style.gap = "8px"; l.style.flex = "0 0 auto";
    const c = document.createElement("input"); c.type = "checkbox"; c.value = String(e.id);
    l.appendChild(c); l.appendChild(crearElemento("span", e.nombre));
    especiesCont.appendChild(l);
    return c;
  });
  tarjeta.appendChild(campo("Nombre", nombre, nombre.id));
  tarjeta.appendChild(labelOb);
  tarjeta.appendChild(crearElemento("div", "Especies aplicables", "campo-etiqueta"));
  tarjeta.appendChild(especiesCont);
  agregarBoton(tarjeta, "Cargar vacuna", async () => {
    try {
      await api("/vacunas", {
        method: "POST",
        body: {
          nombre: nombre.value,
          obligatoria: obligatoria.checked,
          especies_aplicables: checks.filter((c) => c.checked).map((c) => Number(c.value)),
        },
      });
      nombre.value = ""; obligatoria.checked = false; checks.forEach((c) => { c.checked = false; });
      mensaje(mensajes, "Vacuna cargada.", "ok");
      await cargarCatalogos();
    } catch (error) { mensaje(mensajes, error.message, "error"); }
  });
  return tarjeta;
}

export async function montarMascotaDetalle({ params }) {
  const app = document.getElementById("app");
  limpiar(app);
  const id = Number(params.id);
  const mensajes = crearElemento("div");
  try {
    const [mascota, historia] = await Promise.all([
      api(`/mascotas/${id}`),
      api(`/mascotas/${id}/historia-clinica`),
    ]);
    const cliente = await api(`/clientes/${mascota.cliente_id}`).catch(() => null);
    const especie = ESPECIES.find((e) => e.id === mascota.especie_id);
    app.appendChild(vinculo("← Volver a Recepción", "#/recepcion"));
    const cab = crearElemento("section", "", "bloque-intro");
    cab.appendChild(crearElemento("h2", `Mascota: ${mascota.nombre}`));
    cab.appendChild(crearElemento("p", `${especie ? especie.nombre : "Especie"} · Responsable: ${cliente ? cliente.nombre : mascota.cliente_id}`, "texto-secundario"));
    app.appendChild(cab);
    app.appendChild(mensajes);

    const tarjeta = crearTarjeta();
    tarjeta.appendChild(pestanas([
      { id: "datos", titulo: "Datos e historia", render: (p) => tabDatosMascota(p, mascota, historia, cliente, especie) },
      { id: "vacunas", titulo: "Vacunas", render: (p) => tabVacunasMascota(p, historia, mensajes) },
      { id: "consultas", titulo: "Consultas", render: (p) => tabConsultasMascota(p, mascota) },
      { id: "turnos", titulo: "Turnos", render: (p) => tabTurnosMascota(p, mascota) },
    ], "datos"));
    app.appendChild(tarjeta);
  } catch (error) { mensaje(app, error.message, "error"); }
}

async function tabDatosMascota(panel, mascota, historia, cliente, especie) {
  limpiar(panel);
  const dl = crearElemento("dl", "", "lista-datos");
  [
    ["ID", mascota.id], ["Nombre", mascota.nombre], ["Especie", especie ? especie.nombre : mascota.especie_id],
    ["Fecha nacimiento", mascota.fecha_nacimiento], ["Responsable", cliente ? cliente.nombre : mascota.cliente_id],
    ["Historia clínica", historia.numero], ["Activa", mascota.activo ? "Sí" : "No"],
  ].forEach(([dt, dd]) => { dl.appendChild(crearElemento("dt", dt)); dl.appendChild(crearElemento("dd", String(dd))); });
  panel.appendChild(dl);
  const acciones = crearElemento("div", "", "bloque-acciones");
  agregarBoton(acciones, "Descargar carnet PDF", async () => {
    try { await descargarPdf(`/mascotas/${mascota.id}/carnet-vacunas`, `carnet-vacunas-${mascota.id}.pdf`); }
    catch (e) { mensaje(panel, e.message, "error"); }
  }, "boton boton-secundario");
  panel.appendChild(acciones);
}

async function tabVacunasMascota(panel, historia, mensajesGlobal) {
  limpiar(panel);
  const local = crearElemento("div");
  panel.appendChild(local);
  try {
    const [pendientes, aplicadas, vacunas] = await Promise.all([
      api(`/historias-clinicas/${historia.id}/vacunas-pendientes`),
      api(`/historias-clinicas/${historia.id}/vacunaciones`),
      api("/vacunas"),
    ]);
    if (pendientes.length) {
      const aviso = crearElemento("div", "", "aviso");
      aviso.appendChild(crearElemento("strong", "Vacunas pendientes: "));
      aviso.appendChild(document.createTextNode(pendientes.map((v) => v.nombre).join(", ")));
      panel.appendChild(aviso);
    } else {
      panel.appendChild(crearElemento("p", "No hay vacunas obligatorias pendientes.", "mensaje mensaje-ok"));
    }

    const form = crearElemento("div", "", "seccion");
    form.appendChild(crearElemento("h3", "Registrar vacunación"));
    const fila = crearElemento("div", "", "fila");
    const selVac = selectOpciones(vacunas, { placeholder: "Seleccionar vacuna…" }); selVac.id = `vac-${historia.id}`;
    const fecha = entradaTexto("", "date"); fecha.id = `vac-fecha-${historia.id}`;
    fila.appendChild(campo("Vacuna", selVac, selVac.id));
    fila.appendChild(campo("Fecha", fecha, fecha.id));
    form.appendChild(fila);
    agregarBoton(form, "Registrar vacunación", async () => {
      try {
        await api(`/historias-clinicas/${historia.id}/vacunaciones`, {
          method: "POST", body: { vacuna_id: Number(selVac.value), fecha: fecha.value },
        });
        mensaje(mensajesGlobal, "Vacunación registrada.", "ok");
        await tabVacunasMascota(panel, historia, mensajesGlobal);
      } catch (e) { mensaje(local, e.message, "error"); }
    });
    panel.appendChild(form);

    const sec = crearElemento("div", "", "seccion");
    sec.appendChild(crearElemento("h3", "Vacunas aplicadas"));
    if (!aplicadas.length) textoOVacio(sec, "No hay vacunaciones registradas.");
    else sec.appendChild(tabla(["Id", "Vacuna", "Fecha"], aplicadas.map((a) => [a.id, (vacunas.find((v) => v.id === a.vacuna_id) || {}).nombre || a.vacuna_id, a.fecha])));
    panel.appendChild(sec);
  } catch (error) { mensaje(panel, error.message, "error"); }
}

async function tabConsultasMascota(panel, mascota) {
  limpiar(panel);
  try {
    const consultas = await api(`/consultas?mascota_id=${mascota.id}`);
    if (!consultas.length) { textoOVacio(panel, "Esta mascota no tiene consultas registradas."); return; }
    panel.appendChild(tabla(
      ["N°", "Fecha", "Complejidad", "Costo", "Ficha"],
      consultas.map((c) => [c.numero, c.fecha, c.complejidad, c.costo, vinculo("Ver", `#/consultas/${c.id}`)]),
    ));
  } catch (error) { mensaje(panel, error.message, "error"); }
}

async function tabTurnosMascota(panel, mascota) {
  limpiar(panel);
  panel.appendChild(crearElemento("p", "Los turnos se consultan bajo demanda para no cargar agendas innecesariamente.", "texto-secundario"));
  const cont = crearElemento("div", "", "seccion");
  panel.appendChild(cont);
  agregarBoton(panel, "Cargar turnos", async () => {
    limpiar(cont);
    cont.appendChild(crearElemento("p", "Cargando turnos…", "texto-secundario"));
    try {
      await cargarCatalogos();
      await cargarTodosVeterinarios();
      const { veterinariosPorClinica } = obtenerEstado();
      const vets = Object.values(veterinariosPorClinica).flat();
      const agendas = await Promise.all(vets.map((v) => api(`/veterinarios/${v.id}/agenda`).then((ts) => ts.map((t) => ({ ...t, veterinario: v }))).catch(() => [])));
      const turnos = agendas.flat().filter((t) => t.mascota_id === mascota.id);
      limpiar(cont);
      if (!turnos.length) { textoOVacio(cont, "No hay turnos para esta mascota."); return; }
      cont.appendChild(tabla(
        ["Id", "Veterinario", "Inicio", "Fin", "Activo"],
        turnos.map((t) => [t.id, `${t.veterinario.nombre} (${t.veterinario.matricula})`, formatearFechaHora(t.inicio), formatearFechaHora(t.fin), t.activo ? "Sí" : "No"]),
      ));
    } catch (error) { limpiar(cont); mensaje(cont, error.message, "error"); }
  }, "boton boton-secundario");
}
