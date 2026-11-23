/* Login: obtiene token y lo guarda en sessionStorage. */
import { api, guardarSesion, haySesion } from "../api.js";
import { agregarBoton, campo, crearElemento, crearTarjeta, entradaTexto, limpiar, mensaje } from "../ui.js";

export async function montarLogin() {
  if (haySesion()) {
    window.location.hash = "#/inicio";
    return;
  }

  const app = document.getElementById("app");
  limpiar(app);

  const intro = crearElemento("section", "", "bloque-intro");
  intro.appendChild(crearElemento("h2", "Iniciar sesión"));
  intro.appendChild(crearElemento("p", "Ingresá con tu usuario para acceder al sistema.", "texto-secundario"));
  app.appendChild(intro);

  const tarjeta = crearTarjeta("Acceso");
  const mensajes = crearElemento("div");
  tarjeta.appendChild(mensajes);

  const usuario = entradaTexto("Usuario");
  usuario.id = "login-usuario";
  usuario.autocomplete = "username";
  const contrasena = entradaTexto("Contraseña", "password");
  contrasena.id = "login-contrasena";
  contrasena.autocomplete = "current-password";

  tarjeta.appendChild(campo("Usuario", usuario, usuario.id));
  tarjeta.appendChild(campo("Contraseña", contrasena, contrasena.id));

  const acciones = crearElemento("div", "", "bloque-acciones");
  agregarBoton(acciones, "Ingresar", async () => {
    limpiar(mensajes);
    try {
      const respuesta = await api("/auth/login", {
        method: "POST",
        body: { usuario: usuario.value, contrasena: contrasena.value },
      });
      guardarSesion({
        token: respuesta.token,
        rol: respuesta.rol,
        usuario: usuario.value.trim(),
      });
      window.location.hash = "#/inicio";
    } catch (error) {
      mensaje(mensajes, error.message, "error");
    }
  });
  tarjeta.appendChild(acciones);
  app.appendChild(tarjeta);
}
