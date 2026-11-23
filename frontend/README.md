# Frontend

Frontend mínimo en **HTML + JavaScript puro** (sin frameworks, sin librerías, sin npm), servido por FastAPI en `/app`.

## Cómo levantar

Desde la carpeta `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

> **Importante:** no usar `--reload`. El modo reload puede interferir con la base SQLite durante la demo.

Luego abrir en el navegador:

- Frontend: `http://localhost:8000/app/`
- Swagger: `http://localhost:8000/docs`

Si el frontend se ve desactualizado, hacer recarga dura con **Ctrl+F5**.

## Autenticación

- El sistema exige inicio de sesión. Sin sesión, cualquier ruta redirige a `#/login`.
- El token se guarda en `sessionStorage` y se envía en `Authorization: Bearer <token>`.
- Si la API responde 401, el frontend limpia la sesión y vuelve al login.
- Al iniciar la app (fuera de tests), si no existe, se crea el usuario `admin` con rol `ADMIN`.
- Contraseña inicial por defecto de desarrollo: `admin123` (o la variable de entorno `ADMIN_PASSWORD`).
- La clave de firma de tokens sale de `SECRET_KEY` (por defecto de desarrollo). Cambiar ambas en entornos reales.

## Estructura

- `index.html`: shell con sidebar, sesión y contenedor `#app`.
- `css/estilos.css`: estilos del diseño aprobado.
- `js/api.js`: envoltorio de fetch, auth/sesión, manejo de errores y descarga de PDFs.
- `js/ui.js`: helpers de DOM (todo texto dinámico con `textContent`).
- `js/estado.js`: catálogos compartidos (especies hardcodeadas con TODO).
- `js/router.js`: router por hash con guard de sesión.
- `js/app.js`: registro de rutas, menú, sesión y arranque.
- `js/vistas/`: una vista por área funcional, incluyendo `login.js`.

## Notas

- Las especies están hardcodeadas en `js/estado.js` con un `TODO` hasta que el backend exponga `GET /api/especies`.
- Los turnos de una mascota se cargan bajo demanda con el botón “Cargar turnos”.
- Para rol `VETERINARIO`, se ocultan botones de alta/edición/baja de clínicas y veterinarios; la protección real es del backend.
- Los errores del backend se muestran en español; 401/403/409 se muestran visibles en pantalla.