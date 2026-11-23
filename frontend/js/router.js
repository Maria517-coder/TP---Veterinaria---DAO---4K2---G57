/* Router por hash: soporta rutas estáticas y con :param. */
import { haySesion } from "./api.js";

const rutas = [];

export function registrarRuta(patron, render) {
  const nombres = [];
  const regex = new RegExp(
    "^" +
      patron.replace(/:([a-zA-Z]+)/g, (_, nombre) => {
        nombres.push(nombre);
        return "([^/]+)";
      }) +
      "$",
  );
  rutas.push({ patron, regex, nombres, render });
}

function parsearHash() {
  const limpio = window.location.hash.replace(/^#/, "") || "/inicio";
  const [ruta] = limpio.split("?");
  return ruta.startsWith("/") ? ruta : `/${ruta}`;
}

export function navegar(ruta) {
  window.location.hash = ruta.startsWith("#") ? ruta : `#${ruta}`;
}

export function obtenerRutaActual() {
  return parsearHash();
}

async function resolver() {
  const ruta = parsearHash();
  if (ruta !== "/login" && !haySesion()) {
    navegar("/login");
    return;
  }
  for (const entrada of rutas) {
    const coincide = ruta.match(entrada.regex);
    if (coincide) {
      const params = {};
      entrada.nombres.forEach((nombre, indice) => {
        params[nombre] = decodeURIComponent(coincide[indice + 1]);
      });
      await entrada.render({ ruta, params });
      return;
    }
  }
  navegar(haySesion() ? "/inicio" : "/login");
}

export function iniciarRouter() {
  window.addEventListener("hashchange", () => {
    resolver().catch((error) => {
      const app = document.getElementById("app");
      if (app) {
        while (app.firstChild) app.removeChild(app.firstChild);
        const aviso = document.createElement("p");
        aviso.className = "mensaje mensaje-error";
        aviso.textContent = error.message || "Error al cargar la pantalla.";
        app.appendChild(aviso);
      }
    });
  });
  return resolver();
}
