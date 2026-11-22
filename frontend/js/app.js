/* Punto de entrada: sidebar, rutas y arranque del router. */
import { iniciarRouter, obtenerRutaActual, registrarRuta } from "./router.js";
import { montarInicio } from "./vistas/inicio.js";

const TITULOS = {
  inicio: "Inicio",
  clinicas: "Red y clínicas",
  recepcion: "Recepción",
  consultorio: "Consultorio",
  turnos: "Turnos",
  laboratorio: "Laboratorio y envíos",
  reportes: "Reportes",
};

function areaDeRuta(ruta) {
  const partes = ruta.split("/").filter(Boolean);
  return partes[0] || "inicio";
}

function actualizarMenu() {
  const area = areaDeRuta(obtenerRutaActual());
  document.querySelectorAll(".menu-item").forEach((enlace) => {
    const activa = enlace.dataset.ruta === area;
    enlace.classList.toggle("activo", activa);
    if (activa) {
      enlace.setAttribute("aria-current", "page");
    } else {
      enlace.removeAttribute("aria-current");
    }
  });
  const titulo = document.getElementById("titulo-seccion");
  if (titulo) titulo.textContent = TITULOS[area] || "Red veterinaria";
}

function registrarPlaceholder(patron, nombre) {
  registrarRuta(patron, async () => {
    actualizarMenu();
    const app = document.getElementById("app");
    while (app.firstChild) app.removeChild(app.firstChild);
    const tarjeta = document.createElement("section");
    tarjeta.className = "tarjeta";
    const h2 = document.createElement("h2");
    h2.textContent = nombre;
    const p = document.createElement("p");
    p.className = "texto-secundario";
    p.textContent = "Esta sección se implementa en una tanda próxima.";
    tarjeta.appendChild(h2);
    tarjeta.appendChild(p);
    app.appendChild(tarjeta);
  });
}

async function iniciar() {
  registrarRuta("/inicio", async (ctx) => {
    actualizarMenu();
    await montarInicio(ctx);
  });

  registrarPlaceholder("/clinicas", "Red y clínicas");
  registrarPlaceholder("/clinicas/:id", "Ficha de clínica");
  registrarPlaceholder("/recepcion", "Recepción");
  registrarPlaceholder("/mascotas/:id", "Ficha de mascota");
  registrarPlaceholder("/consultorio", "Consultorio");
  registrarPlaceholder("/consultas/:id", "Ficha de consulta");
  registrarPlaceholder("/turnos", "Turnos");
  registrarPlaceholder("/laboratorio", "Laboratorio y envíos");
  registrarPlaceholder("/contenedores/:id", "Ficha de contenedor");
  registrarPlaceholder("/remitos/:id", "Ficha de remito");
  registrarPlaceholder("/muestras/:id", "Ficha de muestra");
  registrarPlaceholder("/reportes", "Reportes");

  await iniciarRouter();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    iniciar().catch(mostrarFalloArranque);
  });
} else {
  iniciar().catch(mostrarFalloArranque);
}

function mostrarFalloArranque(error) {
  const app = document.getElementById("app");
  if (!app) return;
  while (app.firstChild) app.removeChild(app.firstChild);
  const aviso = document.createElement("p");
  aviso.className = "mensaje mensaje-error";
  aviso.textContent = error.message || "No se pudo iniciar la aplicación.";
  app.appendChild(aviso);
}
