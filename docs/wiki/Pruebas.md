# Pruebas

## Ejecutar

```bash
source .venv/bin/activate
python -m pytest -q
```

`pytest.ini` fija `pythonpath = .` para que `from app.main import create_app` funcione sin instalar el paquete.

## Casos actuales (`tests/test_main.py`)

| Prueba | Qué cubre |
| --- | --- |
| `test_create_question_and_state` | creación, normalización de espacios y estado |
| `test_panelist_answer_generates_related_ai_followup` | follow-up de IA ligado por `context_question_id` |
| `test_manual_ai_answer_and_five_summaries` | respuesta IA manual y 5 resúmenes siempre presentes |
| `test_vote_and_missing_question` | votos y `404` en pregunta inexistente |
| `test_demo_state_contains_context_and_summary_data` | semilla de demo con contexto completo |

Todas usan `TestClient(create_app(seed_demo=False))` (aislamiento por app nueva); solo la última usa la demo sembrada.

## Añadir un caso

```python
def test_reset_clears_session() -> None:
    with make_client() as client:
        client.post("/api/questions", json={"text": "¿Qué pasó ayer?"})
        state = client.post("/api/reset").json()
        assert state["questions"] == []
```

Consejo: crea la app por test (`create_app`) en vez de importar `app.main.app`, que viene sembrada.

## Errores conocidos

- `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`: aviso de la versión instalada de Starlette; no afecta a los resultados.
