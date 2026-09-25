from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import PanelistAnswerCreate, QuestionCreate
from .services import SessionStore


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


def create_app(seed_demo: bool = True) -> FastAPI:
    application = FastAPI(
        title="Foro Vivo",
        description="Foro participativo con panelists y respuestas de IA simuladas.",
        version="0.1.0",
    )
    store = SessionStore(seed_demo=seed_demo)
    application.state.store = store
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/state")
    async def state() -> dict[str, object]:
        return store.public_state()

    @application.get("/api/analytics")
    async def analytics() -> dict[str, object]:
        return store.analytics()

    @application.post("/api/questions", status_code=201)
    async def create_question(payload: QuestionCreate) -> dict[str, object]:
        question = store.add_question(payload.text, payload.author)
        return store.question_to_dict(question)

    @application.post("/api/questions/{question_id}/vote")
    async def vote_for_question(question_id: str) -> dict[str, object]:
        question = store.add_vote(question_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        return store.question_to_dict(question)

    @application.post("/api/questions/{question_id}/panelist-answer")
    async def answer_as_panelist(
        question_id: str, payload: PanelistAnswerCreate
    ) -> dict[str, object]:
        result = store.add_panelist_answer(question_id, payload.panelist, payload.text)
        if result is None:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        question, answer = result
        followup_result = store.add_ai_followup(question.id)
        followup = None
        if followup_result is not None:
            followup_question, followup_answer, source_question = followup_result
            followup = {
                "question": store.question_to_dict(followup_question),
                "answer": store.answer_to_dict(followup_answer),
                "source_question": source_question.text,
            }
        return {
            "question": store.question_to_dict(question),
            "answer": store.answer_to_dict(answer),
            "ai_followup": followup,
        }

    @application.post("/api/questions/{question_id}/ai-answer")
    async def answer_with_ai(question_id: str) -> dict[str, object]:
        result = store.add_ai_answer(question_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        question, answer, context, created = result
        return {
            "question": store.question_to_dict(question),
            "answer": store.answer_to_dict(answer),
            "context_question": store.question_to_dict(context),
            "created": created,
        }

    @application.post("/api/reset")
    async def reset_session() -> dict[str, object]:
        store.reset()
        return store.public_state()

    return application


app = create_app()
