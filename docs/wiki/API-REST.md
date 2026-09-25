# API REST

Base URL: `http://127.0.0.1:8000`. Swagger en `/docs`.

## Salud

```http
GET /api/health
```

```json
{"status": "ok"}
```

## Estado completo

```http
GET /api/state
```

Devuelve `questions` (con `keywords` y `answers` por pregunta), `panelists` y `analytics`.

## Analítica

```http
GET /api/analytics
```

```json
{
  "stats": {"questions": 5, "responses": 5, "panelist_responses": 5, "ai_responses": 0, "answered_questions": 5, "keywords": 12},
  "keywords": [{"word": "campana", "count": 3}],
  "summaries": [{"id": "summary_q_...", "title": "Tema: campana", "summary": "...", "available": true}],
  "context": {"source_question": "...", "panelist": "Elena Ruiz", "panelist_answer": "...", "ai_question": null, "ai_answer": null}
}
```

`summaries` tiene **siempre 5** elementos; si faltan datos se marcan `available: false`.

## Crear pregunta

```http
POST /api/questions
Content-Type: application/json

{"text": "¿Cómo medimos el impacto?", "author": "Ana"}
```

- `201 Created` con la pregunta (`id`, `votes: 0`, `keywords`…).
- `422` si el texto mide menos de 3 o más de 280 caracteres.

## Votar

```http
POST /api/questions/{id}/vote
```

Devuelve la pregunta con `votes` incrementado; `404` si el `id` no existe.

## Responder como panelista

```http
POST /api/questions/{id}/panelist-answer
{"panelist": "Elena Ruiz", "text": "Define una línea base y observa los cambios."}
```

Respuesta:

```json
{
  "question": {"...": "pregunta actualizada con has_panelist_answer: true"},
  "answer": {"role": "panelist", "...": "..."},
  "ai_followup": {
    "question": {"...": "nueva pregunta ligada"},
    "answer": {"role": "ai", "context_question_id": "<pregunta fuente>"},
    "source_question": "<texto original>"
  }
}
```

`ai_followup` puede ser `null` si no queda ninguna pregunta relacionada sin respuesta de IA.

## Responder con IA

```http
POST /api/questions/{id}/ai-answer
```

- `answer.role == "ai"`; `context_question_id` apunta a la pregunta de panelista usada como contexto.
- `created: false` si la pregunta ya tenía respuesta de IA (se reutiliza).

## Reiniciar sesión

```http
POST /api/reset
```

Borra todas las preguntas y devuelve el estado vacío.
