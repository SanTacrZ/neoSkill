# Arquitectura

## Visión general

```
 Navegador (static/index.html + app.js)
        │  fetch cada 5 s + acciones POST
        ▼
 FastAPI (app/main.py  → create_app())
        │
        ▼
 SessionStore (app/services.py)
   ├── preguntas / respuestas (dataclasses, lock reentrante)
   ├── IA simulada (_simulated_ai_text)
   ├── palabras clave (extract_keywords)
   ├── 5 resúmenes (build_summaries)
   └── cadena de contexto (context_snapshot)
```

## Módulos

### `app/main.py`

Factoría `create_app(seed_demo=True)`:

- monta `/static` con `StaticFiles`;
- define las rutas de la API (ver [[API-REST]]);
- inyecta el `SessionStore` en `application.state.store`;
- devuelve la instancia `FastAPI` (el objeto `app` a nivel de módulo se crea con la demo sembrada).

### `app/models.py`

Modelos Pydantic de entrada:

- `QuestionCreate`: `text` (3–280) y `author` (2–60).
- `PanelistAnswerCreate`: `panelist` y `text` (3–1200).

Ambos normalizan espacios con un `field_validator` y rechazan textos vacíos.

### `app/services.py`

Aquí está todo el dominio:

| Pieza | Responsabilidad |
| --- | --- |
| `Answer` / `Question` | dataclasses simples, sin ORM |
| `SessionStore` | CRUD de preguntas, votos, respuestas de panelista e IA |
| `extract_keywords()` | tokeniza en español, quita acentos, aplica stopwords y forma canónica (`campanas → campana`) |
| `find_context_question()` | elige la pregunta con respuesta de panelista más relacionada (solape de términos, votos) |
| `_simulated_ai_text()` | redacta la respuesta de IA referenciando al panelista y al tema |
| `add_ai_followup()` | crea la pregunta-followup ligada a la fuente vía `context_question_id` |
| `build_summaries()` | agrupa por palabra clave principal, puntúa (`votos + 4×respuestas`) y devuelve siempre 5 tarjetas (rellena huecos con “pendiente”) |
| `analytics()` / `public_state()` | payloads ya listos para el cliente |

Concurrencia: un `threading.RLock` protege cada operación; el store es compartido entre peticiones del mismo proceso.

### `static/`

- `app.js`: `refresh()` llama a `/api/state`; `setInterval(refresh, 5000)`; delega acciones (votar, responder, IA) en `handleQuestionAction`; persiste borradores con `localStorage`.
- `styles.css`: diseño de una sola página con tarjetas de estadísticas, feed y columna de insights.

## Decisiones de diseño

1. **Renderizado en servidor**: nube de palabras, resúmenes y contexto se calculan en Python y llegan al cliente como JSON listo para pintar (menos lógica en el navegador, mismo cálculo para cualquier cliente futuro: app de control, app de experto, presentación…).
2. **Estado en memoria**: suficiente para una sesión de clase; un reinicio = `POST /api/reset`.
3. **IA como dependencia reemplazable**: los endpoints no cambian al conectar un modelo real.
4. **Sin base de datos**: cero configuración para arrancar la demo.
