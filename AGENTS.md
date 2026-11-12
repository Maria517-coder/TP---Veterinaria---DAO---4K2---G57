# AGENTS.md – Guía de trabajo para el asistente de código

## Contexto
TP Integrador de Desarrollo de Aplicaciones con Objetos (UTN), Tema 2: red de clínicas veterinarias que deriva muestras biológicas a un laboratorio central, con trazabilidad completa de cada muestra.
La usuaria es **estudiante y está aprendiendo cómo se construye un full stack**. Tu trabajo es programar, pero también que ella entienda lo que hacés. Un código que ella no puede explicar no sirve para este TP.

## Modo de trabajo (obligatorio)
1. **Un paso por vez.** No te adelantes a otros módulos ni a otras capas. Si el pedido es "el CRUD de clientes", no toques mascotas.
2. **Plan antes de codear.** Antes de crear o modificar archivos, escribí un plan de máximo 5 líneas: qué archivos tocás y por qué. Esperá su OK.
3. **TDD para la lógica de negocio.** Primero el test, mostrale que falla (rojo) y por qué razón; después el código mínimo (verde); después ordenar (refactor). Para los CRUD: al menos un test por endpoint (caso feliz y el error más importante).
4. **Siempre corré `pytest`** después de cambiar código y mostrá el resultado. Si hay tests rotos, arreglalos antes de seguir.
5. **Tandas chicas.** Más de unos 5 archivos por tanda es demasiado: dividí.
6. **Explicá al final, en lenguaje simple:** qué hiciste, por qué en esa capa, y qué concepto aprendió. Cerrá con **2 preguntas de comprensión** para ella.
7. **Git:** nunca hagas `push`, `merge` ni `rebase`. No hagas commits salvo que ella lo pida. Proponé el mensaje de commit con el formato `feat:`, `fix:`, `test:`, `docs:`, `chore:`.
8. **Si algo no está claro, preguntá.** No inventes reglas de negocio, campos ni endpoints: lo que no esté definido va como `# TODO` y se lo consultás.

## Arquitectura en capas (backend/app/)
- `routers/`: reciben la petición, validan con `schemas/`, llaman al service. **Sin reglas de negocio ni SQL.**
- `schemas/`: Pydantic v2, contrato de entrada y salida.
- `services/`: orquestan un caso de uso y manejan la transacción. Deciden poco; delegan en los modelos.
- `repositories/`: consultas y guardado. Sin reglas de negocio.
- `models/`: clases del dominio mapeadas con SQLAlchemy 2.x (estilo 2.0: Mapped/mapped_column). **Las reglas de negocio viven acá.**
- `models/estados/`: patrón **State** (ciclo de vida de la muestra).
- `reportes/`: patrón **Template Method** (`Reporte.generar()` no se sobreescribe; las subclases implementan `obtener_datos` y `calcular`).
- `exceptions/` + `middlewares/manejadores_errores.py`: errores de dominio traducidos a 404, 409 y 422.

## Reglas de negocio (fuente de verdad)
- Toda mascota tiene un responsable (cliente) y exactamente una historia clínica.
- Estados de la muestra: Extraida → Empaquetada → EnTransito → Recibida → Analizada, o EnTransito → Rechazada. Analizada y Rechazada son finales.
- Todo cambio de estado pasa por `MuestraBiologica.cambiar_estado(nuevo, responsable)` y agrega un `CambioEstado`. **El historial es inmutable**: solo se inserta; no hay endpoints ni métodos que lo modifiquen o borren.
- `ContenedorEnvio` (lo físico) solo acepta muestras `Extraida` y todas de la **misma clínica de origen**; al agregarlas pasan a Empaquetada.
- `RemitoBiologico` (el trámite): GENERADO → DESPACHADO → RECIBIDO → CERRADO. Al despachar, las muestras pasan a EnTransito.
- Si el precinto llega roto, las muestras pasan a Rechazada y el remito pasa igual a RECIBIDO.
- `cerrar()` se llama **automáticamente** cuando todas las muestras del contenedor están Analizada o Rechazada. No tiene endpoint.
- `puede_procesarse()` es verdadero solo si la muestra está Recibida.
- Un veterinario no puede tener turnos superpuestos (`Agenda.hay_superposicion`).
- Al registrar una atención se controla el esquema de vacunas obligatorias de la especie.
- Facturación: costo de la consulta + costo de análisis de cada tipo de muestra.

## Dónde está la información
- Atributos, relaciones y firmas: **los archivos de `backend/app/models/`** (la imagen del diagrama de clases no se puede leer: no la uses).
- Lista de endpoints: `docs/endpoints_veterinaria.xlsx` y los `# TODO` de cada router.
- Decisión de diseño: el laboratorio es externo y no se modela como entidad.

## Stack y límites
Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x (estilo 2.0: Mapped/mapped_column), SQLite, pytest + httpx. **No agregues librerías** ni cambies el stack sin consultar. Sin Alembic, sin Docker. El frontend se decide más adelante: no elijas framework por tu cuenta.

## Estilo
Clases en PascalCase (español, como el dominio); archivos, funciones y variables en snake_case. Type hints en todas las firmas y un docstring corto por clase y por método público. Comentarios solo donde el porqué no sea obvio.

## Definición de "terminado"
El paso está terminado cuando: los tests pasan, la app arranca (`uvicorn app.main:app --reload`), `/docs` muestra los endpoints nuevos, no se tocó nada fuera del alcance del paso y ella pudo responder las preguntas de comprensión.
