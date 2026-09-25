from fastapi.testclient import TestClient

from app.main import create_app


def make_client() -> TestClient:
    return TestClient(create_app(seed_demo=False))


def test_create_question_and_state() -> None:
    with make_client() as client:
        response = client.post(
            "/api/questions",
            json={"text": "¿Cómo medimos una experiencia? ", "author": "Ana"},
        )

        assert response.status_code == 201
        question = response.json()
        assert question["text"] == "¿Cómo medimos una experiencia?"
        assert question["votes"] == 0

        state = client.get("/api/state")
        assert state.status_code == 200
        assert len(state.json()["questions"]) == 1


def test_panelist_answer_generates_related_ai_followup() -> None:
    with make_client() as client:
        first = client.post(
            "/api/questions",
            json={"text": "¿Cómo medimos los datos de una campaña?"},
        ).json()
        second = client.post(
            "/api/questions",
            json={"text": "¿Qué datos ayudan a mejorar una campaña?"},
        ).json()

        response = client.post(
            f"/api/questions/{first['id']}/panelist-answer",
            json={"panelist": "Elena Ruiz", "text": "Define una línea base y observa los cambios."},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["question"]["has_panelist_answer"] is True
        assert payload["ai_followup"] is not None
        assert payload["ai_followup"]["question"]["id"] == second["id"]
        assert payload["ai_followup"]["answer"]["role"] == "ai"
        assert payload["ai_followup"]["answer"]["context_question_id"] == first["id"]


def test_manual_ai_answer_and_five_summaries() -> None:
    with make_client() as client:
        question = client.post(
            "/api/questions",
            json={"text": "¿Cómo priorizar un hallazgo?"},
        ).json()

        response = client.post(f"/api/questions/{question['id']}/ai-answer")

        assert response.status_code == 200
        assert response.json()["answer"]["role"] == "ai"
        assert response.json()["created"] is True

        analytics = client.get("/api/analytics").json()
        assert len(analytics["summaries"]) == 5
        assert analytics["stats"]["ai_responses"] == 1
        assert analytics["keywords"]


def test_vote_and_missing_question() -> None:
    with make_client() as client:
        question = client.post("/api/questions", json={"text": "¿Qué aprendemos?"}).json()
        voted = client.post(f"/api/questions/{question['id']}/vote")

        assert voted.status_code == 200
        assert voted.json()["votes"] == 1

        missing = client.post("/api/questions/q_missing/vote")
        assert missing.status_code == 404


def test_demo_state_contains_context_and_summary_data() -> None:
    with TestClient(create_app()) as client:
        state = client.get("/api/state")
        analytics = client.get("/api/analytics")

        assert state.status_code == 200
        assert len(state.json()["questions"]) == 5
        assert analytics.status_code == 200
        assert len(analytics.json()["summaries"]) == 5
        assert analytics.json()["context"]["panelist"]
