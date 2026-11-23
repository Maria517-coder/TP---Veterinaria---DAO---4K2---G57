/* Punto de entrada: sidebar, rutas, guard de sesión y arranque del router. */
import { limpiarSesion, obtenerSesion } from "./api.js";
import { iniciarRouter, obtenerRutaActual, registrarRuta } from "./router.js";
import { crearElemento, limpiar } from "./ui.js";
import { montarClinicaDetalle, montarClinicas } from "./vistas/clinicas.js";
import { montarConsultaDetalle, montarConsultorio } from "./vistas/consultorio.js";
import { montarInicio } from "./vistas/inicio.js";
import {
  montarContenedorDetalle,
  montarLaboratorio,
  montarMuestraDetalle,
  montarRemitoDetalle,
} from "./vistas/laboratorio.js";
import { montarLogin } from "./vistas/login.js";
import { montarMascotaDetalle, montarRecepcion } from "./vistas/recepcion.js";
import { montarReportes } from "./vistas/reportes.js";
import { montarTurnos } from "./vistas/turnos.js";

const TITULOS = {
  login: "Iniciar sesión",
  inicio: "Inicio",
  clinicas: "Red y clínicas",
  recepcion: "Recepción",
  consultorio: "Consultorio",
  turnos: "Turnos",
  laboratorio: "Laboratorio y envíos",
  reportes: "Reportes",
};

const AREA_POR_SEGMENTO = {
  mascotas: "recepcion",
  consultas: "consultorio",
  contenedores: "laboratorio",
  remitos: "laboratorio",
  muestras: "laboratorio",
};

function areaDeRuta(ruta) {
  const partes = ruta.split("/").filter(Boolean);
  const segmento = partes[0] || "inicio";
  return AREA_POR_SEGMENTO[segmento] || segmento;
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

function actualizarSesionSidebar() {
  const cont = document.getElementById("sesion-sidebar");
  if (!cont) return;
  limpiar(cont);
  const sesion = obtenerSesion();
  if (!sesion) {
    cont.classList.add("oculto");
    return;
  }
  cont.classList.remove("oculto");
  const info = crearElemento("p", "", "sesion-info");
  info.textContent = `${sesion.usuario || "Usuario"} (${sesion.rol || ""})`;
  cont.appendChild(info);
  const boton = crearElemento("button", "Cerrar sesión", "boton boton-secundario boton-cerrar-sesion");
  boton.type = "button";
  boton.addEventListener("click", () => {
    limpiarSesion();
    window.location.hash = "#/login";
  });
  cont.appendChild(boton);
}

function actualizarModoLogin() {
  const esLogin = areaDeRuta(obtenerRutaActual()) === "login";
  document.body.classList.toggle("modo-login", esLogin);
}

function registrar(patron, render) {
  registrarRuta(patron, async (ctx) => {
    actualizarModoLogin();
    actualizarMenu();
    actualizarSesionSidebar();
    await render(ctx);
  });
}

async function iniciar() {
  registrar("/login", montarLogin);
  registrar("/inicio", montarInicio);
  registrar("/clinicas", montarClinicas);
  registrar("/clinicas/:id", montarClinicaDetalle);
  registrar("/recepcion", montarRecepcion);
  registrar("/mascotas/:id", montarMascotaDetalle);
  registrar("/consultorio", montarConsultorio);
  registrar("/consultas/:id", montarConsultaDetalle);
  registrar("/turnos", montarTurnos);
  registrar("/laboratorio", montarLaboratorio);
  registrar("/contenedores/:id", montarContenedorDetalle);
  registrar("/remitos/:id", montarRemitoDetalle);
  registrar("/muestras/:id", montarMuestraDetalle);
  registrar("/reportes", montarReportes);

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
