# TP Integrador - Veterinaria (Tema 2)

Sistema para una red de clínicas veterinarias que deriva muestras biológicas a un laboratorio externo, con trazabilidad completa de cada muestra. Trabajo Práctico Integrador de Desarrollo de Aplicaciones con Objetos (UTN).

## Tecnologías

- **Backend:** Python 3.11+ (probado con 3.14), FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x, SQLite.
- **Tests:** pytest + httpx.
- **Frontend:** Flet web con acceso desde `/app/`.
- **Reportes/PDF:** reportlab.

## Requisitos

- Python 3.11 o superior.
- Git.

## Instalación

Desde la raíz del repositorio:

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
pip install -r requirements.txt
```

## Cómo levantar

Desde la carpeta `backend/`, con el entorno virtual activado:

```bash
python -m uvicorn app.main:app
```

En una segunda terminal, prepará el entorno de Flet desde la raíz e iniciá el frontend:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r frontend/requirements.txt
.\venv\Scripts\python.exe -m frontend.main
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- Frontend: `http://127.0.0.1:8000/app/`

> Si cambiás o agregás una columna en un modelo, borrá `backend/veterinaria.sqlite` para que se regenere (los tests usan su propia base y no se ven afectados).

## Credenciales

| Usuario | Contraseña | Rol | Nota |
|---|---|---:|---|
| `admin` | `admin123` | ADMIN | Se crea al iniciar la app (o el valor de `ADMIN_PASSWORD`) |
| `vet1` | `vet12345` | VETERINARIO | Disponible después de cargar los datos de demostración |

## Roles y permisos

| Acción | ADMIN | VETERINARIO |
|---|:---:|:---:|
| Crear/modificar/baja de clínicas, veterinarios, usuarios y tipos de muestra | Sí | No |
| Ver clínicas y veterinarios | Sí | Sí (solo lectura) |
| Clientes, mascotas, vacunas, muestras, contenedores y remitos | Sí | Sí |
| Consultas y turnos | Sí | Solo sobre su propio `veterinario_id` |
| Reportes | Sí | No |

La protección real se aplica en el backend; el frontend solo adapta la navegación.

## Cargar datos de demostración

El script `backend/app/seeds/datos_demo.py` carga datos de ejemplo para la defensa.
No se ejecuta al iniciar la app ni en los tests.

Desde la carpeta `backend/`, con el entorno del proyecto activado:

```bash
python -m app.seeds.datos_demo
```

Qué crea (solo si no existen, busca la clínica "Clínica Central"):
- 2 clínicas: "Clínica Central" y "Clínica Norte".
- 3 veterinarios (2 en Central, 1 en Norte).
- 1 usuario VETERINARIO: `vet1` / `vet12345`.
- 3 clientes y 4 mascotas (perros y gatos).
- Vacunas de catálogo (Rabia, Parvovirus): una mascota con pendientes y otra con carnet completo.
- Consultas del mes actual (costo `100.00`), incluyendo una con vacunas pendientes.
- Muestras en los 6 estados por camino real: Extraída, Empaquetada, En tránsito, Recibida, Analizada y Rechazada.
- 2-3 turnos futuros para distintos veterinarios (anclados a las 10:00 del día siguiente).

El script es idempotente: si ya se cargó, avisa por consola y no duplica datos.

## Cómo correr los tests

Desde la carpeta `backend/`, con el entorno virtual activado:

```bash
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

Los tests usan una base SQLite aparte (`test_veterinaria.sqlite`) y la recrean en cada test.

## Estructura de carpetas

```text
TP-DAO/
├── AGENTS.md
├── README.md
├── .gitattributes
├── backend/
│   ├── app/
│   │   ├── config/        # configuración, base de datos, settings
│   │   ├── core/          # dependencias/auth, seguridad
│   │   ├── exceptions/    # errores de dominio
│   │   ├── middlewares/   # CORS y manejadores de errores
│   │   ├── models/        # modelos SQLAlchemy y patrón State
│   │   ├── reportes/      # generación de reportes/PDF
│   │   ├── repositories/  # acceso a datos (flush, no commit)
│   │   ├── routers/       # endpoints FastAPI
│   │   ├── schemas/       # contratos Pydantic de entrada/salida
│   │   ├── seeds/         # datos iniciales y datos de demo
│   │   └── services/      # casos de uso y transacciones
│   ├── tests/             # tests pytest
│   └── requirements.txt
└── frontend/
    ├── css/
    ├── js/
    │   ├── api.js
    │   ├── app.js
    │   ├── router.js
    │   ├── ui.js
    │   └── vistas/
    └── index.html
```
