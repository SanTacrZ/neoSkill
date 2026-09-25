# neoSkill · Wiki

**neoSkill (Foro Vivo)** es un foro participativo en tiempo real: el público pregunta, los panelistas responden y una IA encadena nuevas preguntas a partir del contexto de la sala, con nube de palabras, resúmenes y votación.

## Índice

- [[Instalación]] — requisitos, clonado y primer arranque.
- [[Arquitectura]] — estructura del proyecto y decisiones de diseño.
- [[API-REST]] — todos los endpoints con ejemplos de petición y respuesta.
- [[Flujo-de-la-sesión]] — ciclo completo: pregunta → panelista → IA → resumen → votación.
- [[Integración-de-IA]] — cómo sustituir la IA simulada por la API de OpenAI (u otra).
- [[Pruebas]] — suite de pytest y cómo añadir casos.

## Arranque rápido

```bash
git clone git@github.com:SanTacrZ/neoSkill.git
cd neoSkill
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Luego abre <http://127.0.0.1:8000>. La demo arranca con 5 preguntas sembradas.

## Ideas clave

| Idea | Dónde vive |
| --- | --- |
| Toda la “magia” de análisis ocurre en el servidor | `app/services.py` |
| El cliente solo pinta estado ya procesado | `static/app.js` (polling cada 5 s) |
| La IA es un cajo intercambiable | `SessionStore._simulated_ai_text()` |
| Validación estricta de entrada | `app/models.py` (Pydantic) |
