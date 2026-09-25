# neoSkill · Foro Vivo

Foro participativo en tiempo real: el público envía preguntas, los panelistas responden y una IA simulada encadena nuevas preguntas y respuestas a partir del contexto de la sala. Todo se alimenta con análisis de palabras clave, 5 resúmenes automáticos y una cadena de contexto que va del panel a la IA.

El backend está pensado para conectarse a cualquier API externa (por ejemplo, la API de OpenAI) detrás de los mismos endpoints: la capa de “IA” está aislada en `app/services.py` y hoy funciona sin claves con una simulación determinista.

## Inspiración: la orquesta completa

Este proyecto es una **práctica académica que simula** un sistema mayor construido en clase, cuya arquitectura real usa la API de OpenAI por detrás, con renderizado en el servidor (nube de palabras incluida) y streaming de imágenes y texto nuevo hacia el cliente.

Ese sistema completo estaba dividido en **varias aplicaciones independientes**:

- una **solo para el experto** (panelista);
- otra **solo para quien maneja la presentación**;
- una app de público/visión (la que aquí emula este foro).

El flujo estaba modelado **como un grafo**: quien controla desde su app decide qué pantalla se muestra en cada momento; cuando todas las fuentes de información están listas, se ejecutan los **mixers** que construyen los resúmenes, se pasan a la pantalla de muestra y, al final, viene la **votación**. Todo ese flujo lo orquesta la app de control: por detrás hay un trabajo robusto y una arquitectura bien diseñada, y esta práctica solo intenta simular esa orquesta completa en un proceso único.

Aquí esa orquesta se condensa en un solo proceso (`SessionStore` + API + vista estática) para poder estudiarla y extenderla:

| Sistema original | Equivalente en este repo |
| --- | --- |
| App del experto | `POST /api/questions/{id}/panelist-answer` |
| App de control de presentación | Orden del feed y acciones sobre `/api/state` |
| Mixers → resúmenes | `SessionStore.build_summaries()` (5 tarjetas) |
| Nube de palabras (render en servidor) | `extract_keywords()` → `/api/analytics` |
| Votación final | `POST /api/questions/{id}/vote` |
| Grafo de fuentes | Preguntas ligadas por `context_question_id` |

## Características

- **Preguntas del público** con autor anónimo, validación de texto y límite de 280 caracteres.
- **Votación** por pregunta (ranking “más votadas” / “recientes”).
- **Respuestas de panelistas** (3 perfiles demo: estrategia, datos y diseño).
- **IA simulada** que:
  - responde a una pregunta usando como contexto la intervención de un panelista relacionado;
  - genera automáticamente un *follow-up* (nueva pregunta + respuesta) vinculada por `context_question_id`.
- **Nube de palabras clave** calculada en el servidor (tokenización en español, sin acentos, *stopwords* y stemming ligero) y renderizada en el cliente.
- **5 resúmenes** construidos en el servidor a partir de los temas con mayor puntaje.
- **Cadena de contexto** “del panel a la IA” visible en la interfaz.
- **Analítica** en vivo (`/api/analytics`) con estadísticas de preguntas, respuestas humanas y de IA.
- **Frontend estático** con *polling* cada 5 s, redacción con borrador persistente y feedback por toast.

## Arquitectura

```
neoSkills/
├── app/
│   ├── main.py        # Factoría create_app() + rutas FastAPI
│   ├── models.py      # Esquemas Pydantic (validación de entrada)
│   └── services.py    # SessionStore: dominio, IA simulada, analítica
├── static/
│   ├── index.html     # Vista única del foro
│   ├── app.js         # Cliente: polling, render, acciones
│   └── styles.css     # Estilos
├── tests/
│   └── test_main.py   # Pruebas de API con TestClient
├── docs/
│   ├── README.md       # Cómo publicar la wiki
│   └── wiki/           # Páginas de la wiki (7 archivos .md)
├── scripts/
│   └── publish-wiki.sh # Publica docs/wiki/ en la wiki de GitHub
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

- **Servidor**: FastAPI + Uvicorn. Todo el renderizado pesado (palabras clave, resúmenes, contexto) ocurre en el servidor y se envía ya listo al cliente.
- **Estado**: `SessionStore` en memoria, con lock reentrante y semilla de demo opcional.
- **Sustituir la IA simulada**: `SessionStore._simulated_ai_text()` es el único punto a reemplazar por una llamada real (p. ej. OpenAI). La firma de los endpoints no cambia.

## Instalación

```bash
git clone git@github.com:SanTacrZ/neoSkill.git
cd neoSkill
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Ejecutar

```bash
uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000>. La app arranca con una demo sembrada (5 preguntas con respuestas de panelista).

Para arrancar vacío monta `create_app(seed_demo=False)` en lugar del `app` de módulo.

## Pruebas

```bash
python -m pytest -q
```

## API REST

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Interfaz del foro |
| `GET` | `/api/health` | Salud del servicio |
| `GET` | `/api/state` | Estado completo (preguntas, panelistas, analítica) |
| `GET` | `/api/analytics` | Palabras clave, 5 resúmenes y cadena de contexto |
| `POST` | `/api/questions` | Crear pregunta `{"text", "author"}` |
| `POST` | `/api/questions/{id}/vote` | Votar una pregunta |
| `POST` | `/api/questions/{id}/panelist-answer` | Responder como panelista `{"panelist", "text"}`; dispara follow-up de IA |
| `POST` | `/api/questions/{id}/ai-answer` | Responder con IA (usa contexto de panel) |
| `POST` | `/api/reset` | Reiniciar la sesión |

Documentación interactiva: <http://127.0.0.1:8000/docs>.

## Wiki

La documentación extendida está en [`docs/wiki/`](docs/README.md): instalación, arquitectura, API, flujo de la sesión, integración de IA y pruebas. Para publicarla en la [wiki de GitHub](https://github.com/SanTacrZ/neoSkill/wiki) (una vez habilitada en *Settings → Features → Wikis*):

```bash
./scripts/publish-wiki.sh
```

## Licencia

Proyecto académico. Uso libre con fines de aprendizaje.
