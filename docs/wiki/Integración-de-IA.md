# Integración de IA

Hoy la IA es **simulada y determinista** (no necesita claves ni red). El objetivo es poder conectar cualquier proveedor —por ejemplo la API de OpenAI— sin tocar los endpoints ni el frontend.

## Punto de sustitución único

`app/services.py` → `SessionStore._simulated_ai_text(target, context)`:

```python
def _simulated_ai_text(self, target: Question, context: Question) -> str:
    # ... lógica actual de palabras clave ...
    return f"{bridge}: para responder a la pregunta sobre {target_focus}, ..."
```

Recibe la pregunta destino y la pregunta de contexto (que incluye la intervención del panelista) y devuelve el texto de la respuesta.

## Esqueleto con OpenAI

```python
import os
from openai import OpenAI

_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def _simulated_ai_text(self, target: Question, context: Question) -> str:
    panelist = self._latest_panelist_answer(context)
    prompt = (
        "Eres panelista de un foro. Responde en español, máximo 4 frases.\n"
        f"Pregunta del público: {target.text}\n"
        f"Intervención previa de {panelist.author}: {panelist.text}\n"
        f"Tema en común: {context.text}"
    )
    completion = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=220,
    )
    return completion.choices[0].message.content.strip()
```

Mismos cambios aplican a `add_ai_followup()` si quieres que la pregunta-followup también la genere el modelo.

## Consideraciones

- **Timeouts**: una llamada de red dentro del lock de `SessionStore` bloquea otras peticiones; para producción, genera fuera del lock o usa un hilo/cola.
- **Coste**: cada `panelist-answer` dispara hasta dos generaciones (respuesta + follow-up). Cachea por hash de `target.id + context.id`.
- **Renderizado en servidor**: la nube de palabras y los resúmenes NO necesitan IA; siguen calculándose en Python, así que solo pagas por los textos.
- **Claves**: nunca subas `OPENAI_API_KEY` al repo; usa el entorno y `.env` ignorado por git.

## Alternativas

La misma interfaz sirve para Ollama local, Anthropic, Gemini o un modelo interno: basta con devolver un `str` desde el mismo método.
