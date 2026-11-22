/*Envoltorio de fetch: unifica errores del backend y descarga PDFs.*/
const BASE = "/api";

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
      return `${status} · ${datos.detalle}`;
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
      return `${status} · ${partes.join("; ")}`;
    }
    if (
      Object.prototype.hasOwnProperty.call(datos, "detail") &&
      typeof datos.detail === "string" &&
      datos.detail.trim()
    ) {
      return `${status} · ${datos.detail}`;
    }
  }
  return `${status} · No se pudo interpretar la respuesta del servidor`;
}

async function responder(respuesta) {
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

  if (body !== undefined) {
    configura.headers["Content-Type"] = "application/json";
    configura.body = JSON.stringify(body);
  }

  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, configura);
  } catch (error) {
    throw new Error("No se pudo conectar con la API. Levantá el servidor desde backend/.");
  }
  return responder(respuesta);
}

export async function descargarPdf(ruta, nombre) {
  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`);
  } catch (error) {
    throw new Error("No se pudo conectar con la API. Levantá el servidor desde backend/.");
  }

  if (!respuesta.ok) return responder(respuesta);

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
