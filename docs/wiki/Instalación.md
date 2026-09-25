# Instalación

## Requisitos

- Python 3.11 o superior (probado en 3.14).
- `git` con acceso SSH a GitHub.

## Pasos

```bash
git clone git@github.com:SanTacrZ/neoSkill.git
cd neoSkill
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` incluye `requirements.txt` (fastapi, uvicorn, pydantic) más `httpx` y `pytest`.

## Arranque

```bash
uvicorn app.main:app --reload
```

- Interfaz: <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/docs>
- Health: `GET /api/health`

### Arrancar sin datos de demo

```python
from fastapi.testclient import TestClient  # o monta create_app(seed_demo=False) en uvicorn
from app.main import create_app

app = create_app(seed_demo=False)
```

## Pruebas

```bash
python -m pytest -q
```

Salida esperada: `5 passed`.

## Variables y configuración

Hoy no hay variables de entorno obligatorias: todo el estado vive en memoria. Si activas un proveedor de IA real, las claves (p. ej. `OPENAI_API_KEY`) se leen desde el entorno — ver [[Integración-de-IA]].
