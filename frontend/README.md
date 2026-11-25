# Frontend web con Flet

La aplicación cubre clínicas, recepción, consultorio, turnos, laboratorio y reportes. Cada página Flet usa su propio cliente HTTP para acceder a FastAPI con el token del usuario. El backend decide los permisos, las reglas de negocio y las transacciones.

## Arranque en Windows

En una terminal, desde `backend/`, iniciá la API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

En otra terminal, desde la raíz, prepará el entorno de Flet una vez:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r frontend/requirements.txt
```

Iniciá el frontend desde la raíz:

```powershell
.\venv\Scripts\python.exe -m frontend.main
```

Abrí [la aplicación](http://localhost:8000/app/). FastAPI redirige al servidor Flet del puerto 8550. Swagger sigue en [/docs](http://localhost:8000/docs) y la versión HTML anterior está en [/app/index.html](http://localhost:8000/app/index.html).

En otra instalación, configurá `FLET_PUBLIC_URL` en el proceso del backend con la dirección pública de Flet y `VETERINARIA_API_URL` en el proceso Flet con la URL de la API, incluido `/api/`.

## Organización

- `main.py` resuelve el inicio de sesión y la navegación por área o ficha.
- `api.py` envía el token y procesa respuestas JSON, PDFs, errores y bajas sin contenido.
- `ui.py` reúne formularios, tablas, navegación y descargas.
- `vistas/` contiene las pantallas que usan esos controles.

## Pruebas del frontend

Desde la raíz, con el entorno Flet:

```powershell
.\venv\Scripts\python.exe -m pip install pytest
.\venv\Scripts\python.exe -m pytest -q frontend/tests
```

La suite de la API se ejecuta desde `backend/` con su propio entorno.
