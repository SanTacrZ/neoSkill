# Flujo de la sesión

El foro está pensado como un grafo de conversación dirigido por quien controla la sala. Estados y transiciones:

```
            ┌────────────────────────────────────────────┐
            ▼                                            │
  [1] Pregunta del público ──votos──▶ [2] Selección      │
            │                                            │
            ▼                                            │
  [3] Respuesta de panelista                             │
            │                                            │
            ├──▶ [4] Follow-up de IA (nueva pregunta     │
            │        ligada por context_question_id) ────┘
            │
            ▼
  [5] Mezcla de fuentes → 5 resúmenes + nube de palabras
            │
            ▼
  [6] Votación final de la sala
```

## 1. El público pregunta

`POST /api/questions`. La pregunta entra al feed ordenada por recientes; cualquiera puede votarla.

## 2. El control de la sala prioriza

El frontend permite ordenar por **recientes** o **más votadas**. En una sesión dirigida, es quien controla la presentación quien decide qué pregunta sube al escenario (la misma API sirve de backend para una app de control separada).

## 3. El panelista responde

`POST /api/questions/{id}/panelist-answer`. Se registra la intervención con autor y texto.

## 4. La IA encadena contexto

Al responder, el servidor:

1. busca la pregunta relacionada con más solape de términos **sin** respuesta de IA;
2. redacta una pregunta-followup y su respuesta (`context_question_id` = pregunta fuente);
3. devuelve todo en `ai_followup`.

También se puede disparar a mano con `POST /api/questions/{id}/ai-answer`.

## 5. Mezcla de fuentes

`GET /api/analytics` ejecuta la “mezcla”:

- **nube de palabras** de todo el corpus (preguntas + respuestas);
- **5 resúmenes** agrupando por palabra clave principal y puntuando por `votos + 4×respuestas`;
- **cadena de contexto**: última intervención de panelista con su follow-up de IA.

## 6. Votación final

Los votos de las preguntas (`POST .../vote`) cierran la sesión: la más votada es la conclusión que se lleva la sala. `POST /api/reset` deja el tablero listo para el siguiente ciclo.

## Consumidores de la misma API

La API es agnóstica al cliente: puede alimentar a la vez

- la vista pública del foro (`static/`),
- una app solo para el experto,
- una app de control de presentación,
- una pantalla de proyección con resúmenes y nube.

Todos leen `/api/state` y `/api/analytics`; el que controla escribe con los `POST`.
