/* Envoltorio de fetch: auth, errores del backend y descarga de PDFs. */
const BASE = "/api";
const CLAVE_SESION = "veterinaria_sesion";

function leerSesion() {
  try {
    const crudo = sessionStorage.getItem(CLAVE_SESION);
    return crudo ? JSON.parse(crudo) : null;
  } catch (_error) {
    return null;
  }
}

export function obtenerSesion() {
  return leerSesion();
}

export function guardarSesion(sesion) {
  try {
    sessionStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
  } catch (_error) {
    // sessionStorage puede no estar disponible; la app seguirá pidiendo login.
  }
}

export function limpiarSesion() {
  try {
    sessionStorage.removeItem(CLAVE_SESION);
  } catch (_error) {
    // sin efecto
  }
}

export function haySesion() {
  const sesion = leerSesion();
  return Boolean(sesion && sesion.token);
}

export function esAdmin() {
  const sesion = leerSesion();
  return Boolean(sesion && sesion.rol === "ADMIN");
}

export function esVeterinario() {
  const sesion = leerSesion();
  return Boolean(sesion && sesion.rol === "VETERINARIO");
}

export function obtenerVeterinarioId() {
  const sesion = leerSesion();
  return sesion ? sesion.veterinario_id : null;
}

export function obtenerClinicaId() {
  const sesion = leerSesion();
  return sesion ? sesion.clinica_id : null;
}

function rutaLegible(loc) {
  if (!Array.isArray(loc)) return "";
  return loc
    .filter((parte) => !["body", "query", "path"].includes(String(parte)))
    .join(".");
}

export function formatearError(datos, status) {
  if (datos && typeof datos === "object") {
    if (
      Object.prototype.hasOwnProperty.call(datos, "detalle") &&
      typeof datos.detalle === "string" &&
      datos.detalle.trim()
    ) {
      return `${status} - ${datos.detalle}`;
    }
    if (
      Object.prototype.hasOwnProperty.call(datos, "detail") &&
      Array.isArray(datos.detail)
    ) {
      const partes = datos.detail.map((item) => {
        const ruta = rutaLegible(item && item.loc);
        const mensaje = item && item.msg ? item.msg : "Valor inválido";
        return ruta ? `${ruta}: ${mensaje}` : mensaje;
      });
      return `${status} - ${partes.join("; ")}`;
    }
    if (
      Object.prototype.hasOwnProperty.call(datos, "detail") &&
      typeof datos.detail === "string" &&
      datos.detail.trim()
    ) {
      return `${status} - ${datos.detail}`;
    }
  }
  return `${status} - No se pudo interpretar la respuesta del servidor`;
}

function manejar401(ruta) {
  if (ruta === "/auth/login") return false;
  limpiarSesion();
  if (window.location.hash !== "#/login") {
    window.location.hash = "#/login";
  }
  return true;
}

async function responder(respuesta, ruta) {
  if (respuesta.status === 401 && manejar401(ruta)) {
    throw new Error("401 - Sesión vencida o inválida. Volvé a iniciar sesión.");
  }
  if (respuesta.status === 204) return null;

  const tipo = respuesta.headers.get("content-type") || "";
  if (tipo.includes("application/json")) {
    const datos = await respuesta.json().catch(() => null);
    if (!respuesta.ok) throw new Error(formatearError(datos, respuesta.status));
    return datos;
  }

  if (!respuesta.ok) {
    const texto = await respuesta.text().catch(() => "");
    throw new Error(formatearError({ detalle: texto }, respuesta.status));
  }
  return respuesta;
}

export async function api(ruta, opciones = {}) {
  const { method = "GET", body } = opciones;
  const configura = { method, headers: {} };
  const sesion = leerSesion();
  if (sesion && sesion.token) {
    configura.headers["Authorization"] = `Bearer ${sesion.token}`;
  }

  if (body !== undefined) {
    configura.headers["Content-Type"] = "application/json";
    configura.body = JSON.stringify(body);
  }

  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, configura);
  } catch (_error) {
    throw new Error("No se pudo conectar con la API. Levantá el servidor desde backend/.");
  }
  return responder(respuesta, ruta);
}

export async function descargarPdf(ruta, nombre) {
  const sesion = leerSesion();
  const headers = {};
  if (sesion && sesion.token) {
    headers["Authorization"] = `Bearer ${sesion.token}`;
  }
  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, { headers });
  } catch (_error) {
    throw new Error("No se pudo conectar con la API. Levantá el servidor desde backend/.");
  }

  if (respuesta.status === 401 && manejar401(ruta)) {
    throw new Error("401 - Sesión vencida o inválida. Volvé a iniciar sesión.");
  }
  if (!respuesta.ok) return responder(respuesta, ruta);

  const archivo = await respuesta.blob();
  const url = URL.createObjectURL(archivo);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}
