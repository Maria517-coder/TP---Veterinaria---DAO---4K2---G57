/*Pantalla 0: preparar red, clínica, veterinario y vacunas.*/
import { api } from "../api.js";
import { ESPECIES, cargarCatalogos, cargarVeterinarios, obtenerEstado } from "../estado.js";
import {
  agregarBoton,
  campo,
  crearElemento,
  entradaTexto,
  limpiar,
  tabla,
  textoOVacio,
} from "../ui.js";

export function montarSetup({ mostrarError }) {
  const formularios = document.getElementById("formularios");
  const listados = document.getElementById("listados");
  limpiar(formularios);
  limpiar(listados);

  // 1) Clínica
  const nombreClinica = entradaTexto("Nombre de la clínica");
  const bloqueClinica = crearElemento("div", "", "bloque");
  bloqueClinica.appendChild(crearElemento("h3", "1. Clínica"));
  bloqueClinica.appendChild(campo("Nombre", nombreClinica));
  agregarBoton(bloqueClinica, "Crear clínica", async () => {
    try {
      const creada = await api("/red/clinicas", {
        method: "POST",
        body: { nombre: nombreClinica.value },
      });
      nombreClinica.value = "";
      await recargar(creada.id);
    } catch (error) {
      mostrarError(error.message);
    }
  });
  formularios.appendChild(bloqueClinica);

  // 2) Veterinario
  const seleccionClinica = document.createElement("select");
  const matricula = entradaTexto("MP-1234");
  const nombreVeterinario = entradaTexto("Dra. Ana Pérez");
  const bloqueVeterinario = crearElemento("div", "", "bloque");
  bloqueVeterinario.appendChild(crearElemento("h3", "2. Veterinario"));
  bloqueVeterinario.appendChild(campo("Clínica", seleccionClinica));
  bloqueVeterinario.appendChild(campo("Matrícula", matricula));
  bloqueVeterinario.appendChild(campo("Nombre", nombreVeterinario));
  agregarBoton(bloqueVeterinario, "Agregar veterinario", async () => {
    if (!seleccionClinica.value) {
      mostrarError("Primero creá una clínica.");
      return;
    }
    try {
      await api(`/clinicas/${seleccionClinica.value}/veterinarios`, {
        method: "POST",
        body: { matricula: matricula.value, nombre: nombreVeterinario.value },
      });
      matricula.value = "";
      nombreVeterinario.value = "";
      await recargar(seleccionClinica.value);
    } catch (error) {
      mostrarError(error.message);
    }
  });
  seleccionClinica.addEventListener("change", async () => {
    try {
      await cargarVeterinarios(Number(seleccionClinica.value));
      await actualizar();
    } catch (error) {
      mostrarError(error.message);
    }
  });
  formularios.appendChild(bloqueVeterinario);

  // 3) Vacuna
  const nombreVacuna = entradaTexto("Rabia");
  const obligatoria = document.createElement("input");
  obligatoria.type = "checkbox";
  const etiquetaObligatoria = crearElemento("label", "", "opciones");
  etiquetaObligatoria.appendChild(obligatoria);
  etiquetaObligatoria.appendChild(crearElemento("span", " Obligatoria"));

  const opcionesEspecies = crearElemento("div", "", "opciones");
  const casillasEspecies = ESPECIES.map((especie) => {
    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.value = String(especie.id);
    const etiqueta = crearElemento("label", "", "opciones");
    etiqueta.appendChild(casilla);
    etiqueta.appendChild(crearElemento("span", ` ${especie.nombre}`));
    opcionesEspecies.appendChild(etiqueta);
    return casilla;
  });

  const bloqueVacuna = crearElemento("div", "", "bloque");
  bloqueVacuna.appendChild(crearElemento("h3", "3. Vacuna"));
  bloqueVacuna.appendChild(campo("Nombre", nombreVacuna));
  bloqueVacuna.appendChild(etiquetaObligatoria);
  bloqueVacuna.appendChild(crearElemento("p", "Especies aplicables", "campo-etiqueta"));
  bloqueVacuna.appendChild(opcionesEspecies);
  agregarBoton(bloqueVacuna, "Cargar vacuna", async () => {
    const seleccionadas = casillasEspecies
      .filter((casilla) => casilla.checked)
      .map((casilla) => Number(casilla.value));
    try {
      await api("/vacunas", {
        method: "POST",
        body: {
          nombre: nombreVacuna.value,
          obligatoria: obligatoria.checked,
          especies_aplicables: seleccionadas,
        },
      });
      nombreVacuna.value = "";
      casillasEspecies.forEach((casilla) => {
        casilla.checked = false;
      });
      await recargar();
    } catch (error) {
      mostrarError(error.message);
    }
  });
  formularios.appendChild(bloqueVacuna);

  async function actualizar() {
    const datos = obtenerEstado();
    limpiar(listados);

    listados.appendChild(crearElemento("h3", "Estado actual"));
    listados.appendChild(
      crearElemento("p", datos.red ? `Red ${datos.red.id} · ${datos.red.nombre}` : "Sin red configurada"),
    );

    const anterior = seleccionClinica.value;
    limpiar(seleccionClinica);
    datos.clinicas.forEach((clinica) => {
      const opcion = document.createElement("option");
      opcion.value = String(clinica.id);
      opcion.textContent = `${clinica.id} · ${clinica.nombre}`;
      seleccionClinica.appendChild(opcion);
    });
    if (anterior && datos.clinicas.some((clinica) => String(clinica.id) === anterior)) {
      seleccionClinica.value = anterior;
    }

    listados.appendChild(crearElemento("h3", "Clínicas"));
    if (datos.clinicas.length === 0) {
      textoOVacio(listados, "Todavía no hay clínicas.");
    } else {
      listados.appendChild(
        tabla(["Id", "Nombre"], datos.clinicas.map((clinica) => [clinica.id, clinica.nombre])),
      );
    }

    listados.appendChild(crearElemento("h3", "Veterinarios"));
    if (datos.veterinarios.length === 0) {
      textoOVacio(listados, "Elegí una clínica para ver sus veterinarios.");
    } else {
      listados.appendChild(
        tabla(
          ["Id", "Matrícula", "Nombre", "Activo"],
          datos.veterinarios.map((veterinario) => [
            veterinario.id,
            veterinario.matricula,
            veterinario.nombre,
            veterinario.activo ? "sí" : "no",
          ]),
        ),
      );
    }

    listados.appendChild(crearElemento("h3", "Vacunas"));
    if (datos.vacunas.length === 0) {
      textoOVacio(listados, "Todavía no hay vacunas cargadas.");
    } else {
      listados.appendChild(
        tabla(
          ["Id", "Nombre", "Obligatoria", "Especies"],
          datos.vacunas.map((vacuna) => [
            vacuna.id,
            vacuna.nombre,
            vacuna.obligatoria ? "sí" : "no",
            vacuna.especies_aplicables.map((especie) => especie.nombre).join(", "),
          ]),
        ),
      );
    }

    listados.appendChild(crearElemento("h3", "Tipos de muestra (importes como texto)"));
    listados.appendChild(
      tabla(
        ["Id", "Nombre", "Costo de análisis"],
        datos.tiposMuestra.map((tipo) => [tipo.id, tipo.nombre, tipo.costo_analisis]),
      ),
    );
  }

  async function recargar(idClinicaDeseado) {
    const seleccionada = idClinicaDeseado || seleccionClinica.value;
    await cargarCatalogos();
    await actualizar();
    if (seleccionada) {
      seleccionClinica.value = String(seleccionada);
      await cargarVeterinarios(Number(seleccionada));
      await actualizar();
    }
  }

  return actualizar;
}
