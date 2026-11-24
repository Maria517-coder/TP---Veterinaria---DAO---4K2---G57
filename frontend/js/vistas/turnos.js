/* R5: Turnos - agenda, disponibilidad, crear y cancelar. */
import { api, esVeterinario, obtenerClinicaId, obtenerVeterinarioId } from "../api.js";
import { cargarCatalogos, cargarVeterinarios, obtenerEstado } from "../estado.js";
import {
  agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, formatearFechaHora,
  limpiar, llenarSelect, mensaje, selectOpciones, tabla, textoOVacio,
} from "../ui.js";

export async function montarTurnos() {
  const app = document.getElementById("app");
  limpiar(app);

  const intro = crearElemento("section", "", "bloque-intro");
  intro.appendChild(crearElemento("h2", "Turnos"));
  intro.appendChild(crearElemento("p", "Consultá agendas, verificá disponibilidad, creá turnos y cancelalos cuando corresponda.", "texto-secundario"));
  app.appendChild(intro);

  const mensajes = crearElemento("div");
  app.appendChild(mensajes);

  await cargarCatalogos();
  const { clinicas } = obtenerEstado();
  const clientes = await api("/clientes");
  const esVet = esVeterinario();
  const miVetId = obtenerVeterinarioId();

  const tarjetaSel = crearTarjeta("Seleccionar veterinario");
  const selClinica = selectOpciones(clinicas, { placeholder: "Seleccionar clínica…" });
  selClinica.id = "turno-clinica";
  const selVet = selectOpciones([], { placeholder: "Primero seleccioná una clínica…" });
  selVet.id = "turno-vet";
  const fechaAgenda = entradaTexto("", "date");
  fechaAgenda.id = "turno-fecha-agenda";

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
        llenarSelect(selVet, vets, { placeholder: "Seleccionar veterinario.", texto: (v) => `${v.nombre} (${v.matricula})` });
        selVet.value = String(miVetId);
        selVet.disabled = true;
      }
    } catch (_e) { /* protección real en backend */ }
  }

  const filaSel = crearElemento("div", "", "grilla-3");
  filaSel.appendChild(campo("Clínica", selClinica, selClinica.id));
  filaSel.appendChild(campo("Veterinario", selVet, selVet.id));
  filaSel.appendChild(campo("Fecha de agenda (opcional)", fechaAgenda, fechaAgenda.id));
  tarjetaSel.appendChild(filaSel);
  const accSel = crearElemento("div", "", "bloque-acciones");
  tarjetaSel.appendChild(accSel);
  app.appendChild(tarjetaSel);

  const tarjetaAgenda = crearTarjeta("Agenda");
  const contAgenda = crearElemento("div");
  tarjetaAgenda.appendChild(contAgenda);
  app.appendChild(tarjetaAgenda);

  const tarjetaDisp = crearTarjeta("Consultar disponibilidad");
  const dispInicio = entradaTexto("", "datetime-local"); dispInicio.id = "disp-inicio";
  const dispFin = entradaTexto("", "datetime-local"); dispFin.id = "disp-fin";
  const filaDisp = crearElemento("div", "", "grilla-2");
  filaDisp.appendChild(campo("Inicio", dispInicio, dispInicio.id));
  filaDisp.appendChild(campo("Fin", dispFin, dispFin.id));
  tarjetaDisp.appendChild(filaDisp);
  const contDisp = crearElemento("div");
  const accDisp = crearElemento("div", "", "bloque-acciones");
  tarjetaDisp.appendChild(accDisp);
  tarjetaDisp.appendChild(contDisp);
  app.appendChild(tarjetaDisp);

  const tarjetaCrear = crearTarjeta("Crear turno");
  const selCliente = selectOpciones(clientes, { placeholder: "Seleccionar cliente…", texto: (c) => `${c.nombre} (${c.telefono})` });
  selCliente.id = "turno-cliente";
  const selMascota = selectOpciones([], { placeholder: "Seleccionar mascota…" });
  selMascota.id = "turno-mascota";
  const turnoInicio = entradaTexto("", "datetime-local"); turnoInicio.id = "turno-inicio";
  const turnoFin = entradaTexto("", "datetime-local"); turnoFin.id = "turno-fin";
  const filaCrear = crearElemento("div", "", "grilla-2");
  filaCrear.appendChild(campo("Cliente", selCliente, selCliente.id));
  filaCrear.appendChild(campo("Mascota", selMascota, selMascota.id));
  filaCrear.appendChild(campo("Inicio", turnoInicio, turnoInicio.id));
  filaCrear.appendChild(campo("Fin", turnoFin, turnoFin.id));
  tarjetaCrear.appendChild(filaCrear);
  const accCrear = crearElemento("div", "", "bloque-acciones");
  tarjetaCrear.appendChild(accCrear);
  app.appendChild(tarjetaCrear);

  function vetIdActual() {
    const id = Number(selVet.value);
    return id > 0 ? id : null;
  }

  async function cargarAgenda() {
    limpiar(contAgenda);
    const id = vetIdActual();
    if (!id) { textoOVacio(contAgenda, "Seleccioná un veterinario para ver su agenda."); return; }
    contAgenda.appendChild(crearElemento("p", "Cargando agenda…", "texto-secundario"));
    try {
      let ruta = `/veterinarios/${id}/agenda`;
      if (fechaAgenda.value) ruta += `?fecha=${encodeURIComponent(fechaAgenda.value)}`;
      const turnos = await api(ruta);
      limpiar(contAgenda);
      if (!turnos.length) { textoOVacio(contAgenda, "No hay turnos para la selección actual."); return; }
      contAgenda.appendChild(tabla(
        ["Id", "Mascota", "Inicio", "Fin", "Activo", "Acción"],
        turnos.map((t) => {
          const celda = crearElemento("div");
          if (t.activo) {
            agregarBoton(celda, "Cancelar", async () => {
              try {
                await api(`/turnos/${t.id}`, { method: "DELETE" });
                mensaje(mensajes, `Turno ${t.id} cancelado.`, "ok");
                await cargarAgenda();
              } catch (error) {
                mensaje(mensajes, error.message, "error");
              }
            }, "boton boton-peligro");
          } else {
            celda.appendChild(crearElemento("span", "Cancelado", "texto-secundario"));
          }
          return [t.id, t.mascota_id, formatearFechaHora(t.inicio), formatearFechaHora(t.fin), t.activo ? "Sí" : "No", celda];
        }),
      ));
    } catch (error) { limpiar(contAgenda); mensaje(contAgenda, error.message, "error"); }
  }

  selClinica.addEventListener("change", async () => {
    llenarSelect(selVet, [], { placeholder: "Cargando veterinarios…" });
    limpiar(contAgenda);
    try {
      const vets = await cargarVeterinarios(Number(selClinica.value));
      llenarSelect(selVet, vets, { placeholder: "Seleccionar veterinario…", texto: (v) => `${v.nombre} (${v.matricula})` });
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });
  selVet.addEventListener("change", () => { cargarAgenda().catch((e) => mensaje(mensajes, e.message, "error")); });

  selCliente.addEventListener("change", async () => {
    llenarSelect(selMascota, [], { placeholder: "Cargando mascotas…" });
    try {
      const mascotas = await api(`/clientes/${selCliente.value}/mascotas`);
      llenarSelect(selMascota, mascotas, { placeholder: "Seleccionar mascota…" });
    } catch (e) { mensaje(mensajes, e.message, "error"); }
  });

  agregarBoton(accSel, "Ver agenda", cargarAgenda);

  agregarBoton(accDisp, "Consultar disponibilidad", async () => {
    limpiar(contDisp);
    const id = vetIdActual();
    if (!id) { mensaje(contDisp, "Seleccioná un veterinario.", "error"); return; }
    try {
      const params = new URLSearchParams({ inicio: dispInicio.value, fin: dispFin.value });
      const r = await api(`/veterinarios/${id}/turnos/disponibilidad?${params.toString()}`);
      const clase = r.disponible ? "mensaje mensaje-ok" : "mensaje mensaje-error";
      const txt = r.disponible ? "El intervalo está disponible." : "El intervalo no está disponible.";
      contDisp.appendChild(crearElemento("p", txt, clase));
    } catch (e) { mensaje(contDisp, e.message, "error"); }
  }, "boton boton-secundario");

  agregarBoton(accCrear, "Crear turno", async () => {
    const id = vetIdActual();
    if (!id) { mensaje(mensajes, "Seleccioná un veterinario antes de crear el turno.", "error"); return; }
    try {
      await api(`/veterinarios/${id}/turnos`, {
        method: "POST",
        body: {
          mascota_id: Number(selMascota.value),
          inicio: turnoInicio.value,
          fin: turnoFin.value,
        },
      });
      mensaje(mensajes, "Turno creado correctamente.", "ok");
      await cargarAgenda();
    } catch (e) {
      // 409 y otros errores del dominio se muestran visibles aquí.
      mensaje(mensajes, e.message, "error");
    }
  });

  if (esVet && miVetId) {
    cargarAgenda().catch((e) => mensaje(mensajes, e.message, "error"));
  } else {
    textoOVacio(contAgenda, "Seleccion? un veterinario para ver su agenda.");
  }
}
