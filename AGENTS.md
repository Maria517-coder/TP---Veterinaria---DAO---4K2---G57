# AGENTS.md – Guía de trabajo para el asistente de código

## Contexto
TP Integrador de Desarrollo de Aplicaciones con Objetos (UTN), Tema 2: red de clínicas veterinarias que deriva muestras biológicas a un laboratorio externo, con trazabilidad completa de cada muestra.
Quien te usa es **estudiante y está aprendiendo cómo se construye un full stack**. Tu trabajo es programar, pero también que entienda lo que hacés. Un código que no pueda explicar no sirve para este TP.
Este archivo es la fuente común de reglas: **todo el equipo trabaja con las mismas**, así el código queda con el mismo estilo.

## Modo de trabajo (obligatorio)
1. **Un paso por vez.** No te adelantes a otros módulos ni a otras capas. Si el pedido es "el CRUD de clínicas", no toques mascotas.
2. **Plan antes de codear.** Antes de crear o modificar archivos, escribí un plan de máximo 5 líneas: qué archivos tocás y por qué. Esperá el OK.
3. **TDD.** Primero el test, mostrá la salida en **rojo** y explicá por qué falla; después el código mínimo (verde); después ordenar. Por endpoint, al menos el caso feliz y el error más importante. Si un test da verde de entrada, decilo y explicá por qué (por ejemplo, la regla ya estaba en el modelo).
4. **Siempre corré `pytest`** después de cambiar código y mostrá el resultado completo. Si hay tests rotos, arreglalos antes de seguir. Los tests que ya existían tienen que seguir pasando.
5. **Tandas chicas.** Más de unos 5 archivos por tanda es demasiado: dividí.
6. **Explicá al final, en lenguaje simple:** qué hiciste, por qué en esa capa y qué concepto se aprende. Cerrá con **2 preguntas de comprensión**.
7. **Git:** nunca hagas `push`, `merge` ni `rebase`. No hagas commits salvo que te lo pidan. Proponé el mensaje con el formato `feat:`, `fix:`, `test:`, `docs:`, `chore:`.
8. **Si algo no está claro, preguntá.** No inventes reglas de negocio, campos ni endpoints: lo que no esté definido va como `# TODO` y se consulta.

## Entorno
Python 3.11+ (probado con 3.14), FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x (estilo 2.0: `Mapped`/`mapped_column`), SQLite, pytest + httpx. Sin Alembic, sin Docker. **No agregues librerías** ni cambies el stack sin consultar. El frontend se decide en equipo: no elijas framework por tu cuenta.
- Entorno virtual en `backend/.venv`; los tests se corren con `pytest` desde `backend/`.
- En Windows, levantar la app con `python -m uvicorn app.main:app --reload`. `uvloop` se instala solo fuera de Windows (marker en `requirements.txt`).
- **`create_all` no modifica tablas existentes.** Si cambiás o agregás una columna, hay que borrar `backend/veterinaria.sqlite` para que se regenere (avisá antes). Los tests recrean la base en cada test, así que no sufren este problema.

## Arquitectura en capas (backend/app/)
`router → schema → service → repository → model`. Las dependencias bajan, nunca al revés.
- `routers/`: reciben la petici?n, validan con `schemas/`, llaman al service. **Sin reglas de negocio ni SQL.** Cada router se registra en `main.py`, **pero solo cuando sus schemas y services existen y tiene tests**.
- `schemas/`: Pydantic v2, contrato de entrada y salida. No saben de base de datos.
- `services/`: orquestan un caso de uso, deciden, lanzan excepciones de dominio y **manejan la transacción** (`commit`/`rollback`).
- `repositories/`: consultas y guardado. Sin reglas de negocio. **Hacen `flush`, nunca `commit`.** Si algo no existe, devuelven `None`; no lanzan errores.
- `models/`: clases del dominio mapeadas con SQLAlchemy. Las reglas propias del objeto viven acá.
- `models/estados/`: patrón **State** (ciclo de vida de la muestra).
- `reportes/`: patrón **Template Method** (`Reporte.generar()` no se sobreescribe; las subclases implementan `obtener_datos` y `calcular`).
- `exceptions/` + `middlewares/manejadores_errores.py`: errores de dominio traducidos a HTTP. Respuesta de error: `{"detalle": "..."}`.

## Convenciones ya decididas (copiá este estilo)
**Patrón de referencia:** el CRUD de clientes y el de mascotas están terminados y con tests. Antes de escribir algo nuevo, leé `schemas/cliente.py`, `repositories/cliente_repository.py`, `services/cliente_service.py`, `routers/clientes.py` y sus tests (`test_clientes.py`, `test_cliente_service.py`, `test_cliente_repository.py`, `test_schemas_cliente.py`). Para un alta que crea dos objetos juntos, mirá `services/mascota_service.py`.

**Códigos HTTP:** alta `201`; consulta y reemplazo `200`; baja `204` (sin cuerpo); no existe `404` (`RecursoNoEncontrado`); conflicto con el estado actual `409` (`ConflictoDeRecurso`, `TransicionInvalida`, `TurnoSuperpuesto`); dato inválido o regla de negocio `422` (Pydantic o `ReglaDeNegocioViolada`).

**Schemas:** un schema para crear, uno para actualizar y uno de respuesta (`from_attributes=True`). `PUT` es **reemplazo total** (todos los campos obligatorios). Los textos se recortan con `StringConstraints(strip_whitespace=True, ...)` y respetan los largos del modelo. Una regla que depende solo del dato que llega (por ejemplo, fecha de nacimiento no futura) va en el schema; si necesita consultar la base, va en el service.

**Bajas:** son **lógicas** (campo `activo`). Los `GET` devuelven solo activos y un registro inactivo da `404`. Una regla del tipo "no se puede dar de baja si tiene X" cuenta solo los X activos.

**Orden dentro de un service:** primero existencia (`404`), después conflicto (`409`), después mutación y al final el `commit`. Validá todo antes de modificar. Si algo falla, `rollback` y se relanza la excepción.

**Alta conjunta:** si un objeto necesita el `id` de otro (ejemplo: la historia clínica toma el `id` de la mascota), se hace `flush` del primero, se crea el segundo y se confirma todo junto con un solo `commit`.

**Tests:** fixtures `db` (base limpia por test, archivo aparte `test_veterinaria.sqlite`) y `client` (`TestClient` con el `lifespan` activo; siempre con `with`). El repository y el service se prueban directo sobre `db`; el router, por HTTP con `client`.

## Reglas ya implementadas (NO las pises)
- **Seguridad:** roles `ADMIN` y `VETERINARIO`, token firmado HMAC (sin estado), dependencia reutilizable `verificar_propio` para limitar acceso al propio `veterinario_id`, y usuarios vinculados a un veterinario (`Usuario.veterinario_id`).
- **Datos de demo:** `python -m app.seeds.datos_demo` (desde `backend/`) carga datos de ejemplo; es idempotente y **no se ejecuta** al iniciar la app ni en los tests.
- **Codificaci?n:** todo archivo nuevo o modificado se guarda en **UTF-8 sin BOM**. No usar redirecciones de PowerShell (`>`, `Out-File`, `Set-Content` sin `utf8NoBOM`) para escribir c?digo.
- **Importes en `Decimal`**, nunca `float`: dos decimales y redondeo `ROUND_HALF_UP` (ver `models/importes.py`; `normalizar_importe` rechaza `float` y `bool`). Los schemas con importes usan `Decimal`. Pydantic serializa `Decimal` como texto en el JSON: verificalo en un test.
- **El historial de cambios de estado es inmutable**: solo se inserta (triggers de SQLite). No hay endpoints ni métodos que lo modifiquen o borren.
- **Seeds idempotentes**: insertan solo lo que falta (por nombre) y hacen `flush`; el `commit` lo decide el llamador (`lifespan` en `main.py`).
- **Facturación** de `ClinicaVeterinaria`: ya implementada con tests (períodos inclusivos; el laboratorio usa la fecha de la consulta).
- **Clientes, mascotas, historia clínica y vacunas** (E01 a E19) están terminados, con tests. No los rehagas. El carnet de vacunas se genera en PDF con `reportlab` (librería ya aprobada; `pillow` y `charset-normalizer` vienen con ella).

## Reglas de negocio (fuente de verdad)
- Toda mascota tiene un responsable (cliente activo) y exactamente una historia clínica (`numero = mascota.id`).
- Estados de la muestra: Extraida → Empaquetada → EnTransito → Recibida → Analizada, o EnTransito → Rechazada. Analizada y Rechazada son finales.
- Todo cambio de estado pasa por `MuestraBiologica.cambiar_estado(nuevo, responsable)` y agrega un `CambioEstado`.
- `ContenedorEnvio` (lo físico) solo acepta muestras `Extraida` y todas de la **misma clínica de origen**; al agregarlas pasan a Empaquetada.
- `RemitoBiologico` (el trámite): GENERADO → DESPACHADO → RECIBIDO → CERRADO. Al despachar, las muestras pasan a EnTransito.
- Si el precinto llega roto, las muestras pasan a Rechazada y el remito pasa igual a RECIBIDO.
- `cerrar()` se llama **automáticamente** cuando todas las muestras del contenedor están Analizada o Rechazada. No tiene endpoint.
- `puede_procesarse()` es verdadero solo si la muestra está Recibida.
- Un veterinario no puede tener turnos superpuestos (`Agenda.hay_superposicion`; `409` si chocan). La Agenda no tiene tabla: se calcula con los turnos.
- Al registrar una atención se controla el esquema de vacunas obligatorias de la especie.
- Facturación: costo de la consulta + costo de análisis de cada tipo de muestra.
- Decisión de diseño: el laboratorio es externo y no se modela como entidad.

## Dónde está la información
- Atributos, relaciones y firmas: **los archivos de `backend/app/models/`** (las imágenes de diagramas no se pueden leer: no las uses).
- Lista de endpoints, bloques de trabajo y dependencias: el Excel de `docs/` y los `# TODO` de cada router.

## Trabajo en equipo y git
- **Una rama por tarea** (por ejemplo `clinicas`, `turnos`). Nunca se trabaja directo sobre `main`.
- Antes de empezar: `git switch main`, `git pull`, `git switch -c nombre-de-la-rama`.
- Para entregar: `pytest` en verde, commit, `git pull`, `git push -u origin nombre-de-la-rama` y **Pull Request** a `main`, que revisa otra persona.
- Después de cada `pull` en el que haya cambiado un modelo: borrar `backend/veterinaria.sqlite`. Si cambió `requirements.txt`, correr `pip install -r requirements.txt`.
- **Antes de cada commit, mirá `git status` y asegurate de que no queden archivos nuevos sin agregar.** Un router que importa archivos que no se subieron rompe la app para todos (ya pasó con clínicas).
- **Antes de abrir un PR:** `pytest` completo en verde y la app tiene que arrancar (`python -m uvicorn app.main:app`). No subas código que importe módulos inexistentes.
- **No toques sin consultar** los archivos compartidos: `tests/conftest.py`, `main.py`, `exceptions/`, `middlewares/`, `seeds/` ni los modelos existentes. Si hace falta cambiar uno, se avisa antes al equipo.
- El Excel y las imágenes de `docs/` son binarios: si dos personas los editan a la vez, git no los puede mezclar.

## Estilo
Clases en PascalCase (español, como el dominio); archivos, funciones y variables en snake_case. Type hints en todas las firmas y un docstring corto por clase y por método público. Comentarios solo donde el porqué no sea obvio.

## Definición de "terminado"
El paso está terminado cuando: los tests pasan (los nuevos y los que ya existían), la app arranca, `/docs` muestra los endpoints nuevos, no se tocó nada fuera del alcance y quien te usa pudo responder las preguntas de comprensión.

## Plantilla para arrancar una tarea
Pegá esto al empezar, completando lo que está entre corchetes:
```
Leé AGENTS.md y el CRUD de clientes (es el patrón a copiar). Tarea: [bloque o endpoints, por ejemplo "E20 a E31"].
Trabajo en la rama [nombre]. No escribas código todavía: contame en pocas líneas qué entendiste
(arquitectura, reglas que no hay que pisar) y dame un plan de máximo 5 líneas. Esperá mi OK.
Si algo no está definido, preguntame; no lo inventes.
```
