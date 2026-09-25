from __future__ import annotations

import re
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4


PANELISTS = [
    {
        "id": "elena-ruiz",
        "name": "Elena Ruiz",
        "role": "Estrategia de producto",
        "initials": "ER",
        "accent": "coral",
    },
    {
        "id": "mateo-silva",
        "name": "Mateo Silva",
        "role": "Datos y tecnología",
        "initials": "MS",
        "accent": "cyan",
    },
    {
        "id": "sofia-ortiz",
        "name": "Sofía Ortiz",
        "role": "Diseño de experiencias",
        "initials": "SO",
        "accent": "violet",
    },
]

_STOP_WORDS = {
    "about",
    "ahora",
    "algo",
    "algun",
    "alguno",
    "ante",
    "antes",
    "aqui",
    "como",
    "con",
    "contra",
    "cual",
    "cuando",
    "debe",
    "deben",
    "decir",
    "desde",
    "donde",
    "durante",
    "ella",
    "ellos",
    "en",
    "entre",
    "era",
    "es",
    "esta",
    "estaba",
    "estan",
    "estar",
    "este",
    "esto",
    "estos",
    "fue",
    "fueron",
    "ha",
    "haber",
    "hace",
    "hacen",
    "hay",
    "la",
    "las",
    "le",
    "les",
    "lo",
    "los",
    "más",
    "mas",
    "me",
    "mi",
    "mis",
    "mientras",
    "mucho",
    "muy",
    "nada",
    "nunca",
    "nos",
    "nuestra",
    "nuestro",
    "o",
    "otra",
    "otro",
    "para",
    "pero",
    "poco",
    "por",
    "porque",
    "que",
    "quien",
    "quienes",
    "se",
    "segun",
    "ser",
    "si",
    "sin",
    "sobre",
    "solo",
    "son",
    "su",
    "sus",
    "tambien",
    "tanto",
    "te",
    "tiene",
    "tienen",
    "todo",
    "todos",
    "tras",
    "tu",
    "un",
    "una",
    "uno",
    "unos",
    "y",
    "ya",
}

_ALLOWED_SHORT_WORDS = {"api", "ia", "kpi", "roi", "saas"}
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class Answer:
    id: str
    role: str
    author: str
    text: str
    created_at: str
    context_question_id: str | None = None


@dataclass
class Question:
    id: str
    text: str
    author: str
    votes: int
    created_at: str
    answers: list[Answer] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _without_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _canonical_token(token: str) -> str:
    if len(token) > 5 and token.endswith("es"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token


def _tokens(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(_without_accents(text))
    return [
        _canonical_token(token)
        for token in tokens
        if (len(token) >= 4 or token in _ALLOWED_SHORT_WORDS)
        and token not in _STOP_WORDS
        and not token.isdigit()
    ]


def extract_keywords(texts: Iterable[str], limit: int = 12) -> list[dict[str, int | str]]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(_tokens(text))
    return [
        {"word": word, "count": count}
        for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _shorten(value: str, limit: int = 180) -> str:
    clean_value = " ".join(value.split())
    if len(clean_value) <= limit:
        return clean_value
    shortened = clean_value[: limit - 1].rsplit(" ", 1)[0]
    return f"{shortened}…"


def _clean_question(value: str) -> str:
    return value.strip(" ¿?!")


class SessionStore:
    def __init__(self, seed_demo: bool = False) -> None:
        self._lock = threading.RLock()
        self.questions: list[Question] = []
        if seed_demo:
            self._seed_demo()

    def _new_question(self, text: str, author: str, votes: int = 0) -> Question:
        question = Question(
            id=f"q_{uuid4().hex[:10]}",
            text=" ".join(text.split()),
            author=" ".join(author.split()),
            votes=votes,
            created_at=utc_now(),
        )
        self.questions.append(question)
        return question

    def _seed_demo(self) -> None:
        demos = [
            (
                "¿Cómo medir el impacto real de una campaña digital?",
                "Lucía",
                18,
                "Elena Ruiz",
                "Conviene comparar una línea base antes de la campaña con señales posteriores de conversión, calidad y retorno. El dato más útil es el que conecta una decisión concreta con un cambio observable.",
            ),
            (
                "¿Qué señales permiten saber que un modelo de IA es confiable?",
                "Andrés",
                14,
                "Mateo Silva",
                "Revisaría casos representativos, trazabilidad de las decisiones y una revisión humana en los casos sensibles. La confianza se construye con evidencia reproducible, no con una demostración aislada.",
            ),
            (
                "¿Qué herramientas usarían para ordenar hallazgos y prioridades?",
                "Paula",
                11,
                "Sofía Ortiz",
                "Primero agruparía los hallazgos por impacto y esfuerzo; después elegiría un tablero breve con responsables, próximos pasos y fecha de revisión.",
            ),
            (
                "¿Cómo puede un equipo pequeño aprender sin perder tiempo cada semana?",
                "Tomás",
                8,
                "Elena Ruiz",
                "Empezaría con una pregunta concreta, una fuente confiable y quince minutos de práctica. La práctica breve convierte el aprendizaje en un hábito sostenible.",
            ),
            (
                "¿Qué error cometen al medir la satisfacción de los usuarios?",
                "Diana",
                6,
                "Mateo Silva",
                "El error más común es confundir una opinión aislada con una tendencia. Hay que segmentar, escuchar la razón de la respuesta y contrastarla con observaciones del uso real.",
            ),
        ]
        for text, author, votes, panelist, answer in demos:
            question = self._new_question(text, author, votes)
            question.answers.append(
                Answer(
                    id=f"a_{uuid4().hex[:10]}",
                    role="panelist",
                    author=panelist,
                    text=answer,
                    created_at=utc_now(),
                )
            )

    def add_question(self, text: str, author: str) -> Question:
        with self._lock:
            return self._new_question(text, author)

    def get_question(self, question_id: str) -> Question | None:
        with self._lock:
            return self._question_without_lock(question_id)

    def _question_without_lock(self, question_id: str) -> Question | None:
        return next((question for question in self.questions if question.id == question_id), None)

    def add_vote(self, question_id: str) -> Question | None:
        with self._lock:
            question = self._question_without_lock(question_id)
            if question is None:
                return None
            question.votes += 1
            return question

    def add_panelist_answer(self, question_id: str, panelist: str, text: str) -> tuple[Question, Answer] | None:
        with self._lock:
            question = self._question_without_lock(question_id)
            if question is None:
                return None
            answer = Answer(
                id=f"a_{uuid4().hex[:10]}",
                role="panelist",
                author=" ".join(panelist.split()),
                text=" ".join(text.split()),
                created_at=utc_now(),
            )
            question.answers.append(answer)
            return question, answer

    def _question_terms(self, question: Question) -> set[str]:
        text_parts = [question.text]
        text_parts.extend(answer.text for answer in question.answers)
        return set(_tokens(" ".join(text_parts)))

    def _latest_panelist_answer(self, question: Question) -> Answer | None:
        return next(
            (answer for answer in reversed(question.answers) if answer.role == "panelist"),
            None,
        )

    def _has_ai_answer(self, question: Question) -> bool:
        return any(answer.role == "ai" for answer in question.answers)

    def find_related_question(self, source_question_id: str) -> Question | None:
        with self._lock:
            source = self._question_without_lock(source_question_id)
            if source is None:
                return None
            source_terms = self._question_terms(source)
            candidates = [
                question
                for question in self.questions
                if question.id != source_question_id
            ]
            if not candidates:
                return None
            scored = []
            for index, question in enumerate(candidates):
                overlap = len(source_terms & self._question_terms(question))
                if overlap:
                    scored.append(
                        (
                            overlap,
                            0 if self._has_ai_answer(question) else 1,
                            question.votes,
                            -index,
                            question,
                        )
                    )
            if not scored:
                return None
            scored.sort(key=lambda item: item[:4], reverse=True)
            return scored[0][4]

    def find_context_question(self, target_question_id: str) -> Question:
        with self._lock:
            target = self._question_without_lock(target_question_id)
            if target is None:
                raise KeyError(target_question_id)
            candidates = [
                question
                for question in self.questions
                if question.id != target_question_id and self._latest_panelist_answer(question)
            ]
            if not candidates:
                return target
            target_terms = self._question_terms(target)
            scored = []
            for index, question in enumerate(candidates):
                overlap = len(target_terms & self._question_terms(question))
                scored.append((overlap, question.votes, -index, question))
            scored.sort(key=lambda item: item[:3], reverse=True)
            return scored[0][3]

    def _simulated_ai_text(self, target: Question, context: Question) -> str:
        target_keywords = extract_keywords([target.text], limit=4)
        context_keywords = extract_keywords(
            [context.text, *(answer.text for answer in context.answers)], limit=6
        )
        target_words = [item["word"] for item in target_keywords]
        context_words = [item["word"] for item in context_keywords]
        shared_words = [word for word in target_words if word in context_words]
        focus = shared_words[0] if shared_words else (context_words[0] if context_words else "el contexto")
        target_focus = target_words[0] if target_words else "esta pregunta"
        context_answer = self._latest_panelist_answer(context)
        if context_answer is not None:
            bridge = f"Tomo como referencia la intervención de {context_answer.author} sobre {focus}"
        else:
            bridge = f"Uso como referencia el contexto compartido sobre {focus}"
        return (
            f"{bridge}: para responder a la pregunta sobre {target_focus}, separaría el objetivo, "
            "los datos que lo evidences y una revisión breve con el equipo. Así se evita una "
            "conclusión aislada y la idea puede medirse con un siguiente paso concreto."
        )

    def add_ai_answer(self, question_id: str) -> tuple[Question, Answer, Question, bool] | None:
        with self._lock:
            target = self._question_without_lock(question_id)
            if target is None:
                return None
            existing = next((answer for answer in target.answers if answer.role == "ai"), None)
            if existing is not None:
                context = self.find_context_question(question_id)
                return target, existing, context, False
            context = self.find_context_question(question_id)
            answer = Answer(
                id=f"a_{uuid4().hex[:10]}",
                role="ai",
                author="IA simulada",
                text=self._simulated_ai_text(target, context),
                created_at=utc_now(),
                context_question_id=context.id if context.id != target.id else None,
            )
            target.answers.append(answer)
            return target, answer, context, True

    def add_ai_followup(self, source_question_id: str) -> tuple[Question, Answer, Question] | None:
        with self._lock:
            target = self.find_related_question(source_question_id)
            source = self._question_without_lock(source_question_id)
            if target is None or source is None or self._has_ai_answer(target):
                return None
            answer = Answer(
                id=f"a_{uuid4().hex[:10]}",
                role="ai",
                author="IA simulada",
                text=self._simulated_ai_text(target, source),
                created_at=utc_now(),
                context_question_id=source_question_id,
            )
            target.answers.append(answer)
            return target, answer, source

    def _question_keywords(self, question: Question) -> list[dict[str, int | str]]:
        return extract_keywords(
            [question.text, *(answer.text for answer in question.answers)], limit=5
        )

    def _summary_candidates(self) -> list[dict[str, object]]:
        candidates: dict[str, dict[str, object]] = {}
        for question in self.questions:
            keywords = self._question_keywords(question)
            keyword = str(keywords[0]["word"]) if keywords else "participación"
            answer = question.answers[-1] if question.answers else None
            score = question.votes + (len(question.answers) * 4)
            candidate = {
                "keyword": keyword,
                "question": question,
                "answer": answer,
                "score": score,
            }
            current = candidates.get(keyword)
            if current is None or score > int(current["score"]):
                candidates[keyword] = candidate
        return sorted(candidates.values(), key=lambda item: int(item["score"]), reverse=True)

    def build_summaries(self, limit: int = 5) -> list[dict[str, object]]:
        summaries: list[dict[str, object]] = []
        for candidate in self._summary_candidates()[:limit]:
            question = candidate["question"]
            answer = candidate["answer"]
            if not isinstance(question, Question):
                continue
            question_text = _clean_question(question.text)
            if isinstance(answer, Answer):
                summary = f"{question_text}. La respuesta más reciente propone: {_shorten(answer.text)}"
                source = answer.author
                role = "IA" if answer.role == "ai" else "Panelista"
                response_count = len(question.answers)
            else:
                summary = f"{question_text}. Esta pregunta todavía espera una respuesta."
                source = "Conversación abierta"
                role = "Pendiente"
                response_count = 0
            summaries.append(
                {
                    "id": f"summary_{question.id}",
                    "question_id": question.id,
                    "title": f"Tema: {candidate['keyword']}",
                    "summary": summary,
                    "source": source,
                    "role": role,
                    "response_count": response_count,
                    "available": True,
                }
            )
        while len(summaries) < limit:
            index = len(summaries) + 1
            summaries.append(
                {
                    "id": f"summary_pending_{index}",
                    "question_id": None,
                    "title": f"Tema {index}: por descubrir",
                    "summary": "Aún no hay suficientes respuestas para construir este resumen.",
                    "source": "Esperando preguntas",
                    "role": "Pendiente",
                    "response_count": 0,
                    "available": False,
                }
            )
        return summaries

    def context_snapshot(self) -> dict[str, object] | None:
        with self._lock:
            for question in reversed(self.questions):
                panelist_answer = self._latest_panelist_answer(question)
                if panelist_answer is None:
                    continue
                followup_question = next(
                    (
                        other
                        for other in self.questions
                        if any(
                            answer.role == "ai" and answer.context_question_id == question.id
                            for answer in other.answers
                        )
                    ),
                    None,
                )
                followup_answer = (
                    next(
                        (
                            answer
                            for answer in followup_question.answers
                            if answer.role == "ai" and answer.context_question_id == question.id
                        ),
                        None,
                    )
                    if followup_question is not None
                    else None
                )
                return {
                    "source_question": question.text,
                    "panelist": panelist_answer.author,
                    "panelist_answer": panelist_answer.text,
                    "ai_question": followup_question.text if followup_question else None,
                    "ai_answer": followup_answer.text if followup_answer else None,
                }
            return None

    def analytics(self) -> dict[str, object]:
        with self._lock:
            texts = []
            for question in self.questions:
                texts.append(question.text)
                texts.extend(answer.text for answer in question.answers)
            keywords = extract_keywords(texts, limit=18)
            all_answers = [answer for question in self.questions for answer in question.answers]
            answered_questions = sum(bool(question.answers) for question in self.questions)
            return {
                "stats": {
                    "questions": len(self.questions),
                    "responses": len(all_answers),
                    "panelist_responses": sum(answer.role == "panelist" for answer in all_answers),
                    "ai_responses": sum(answer.role == "ai" for answer in all_answers),
                    "answered_questions": answered_questions,
                    "keywords": len(keywords),
                },
                "keywords": keywords,
                "summaries": self.build_summaries(),
                "context": self.context_snapshot(),
            }

    def public_state(self) -> dict[str, object]:
        with self._lock:
            analytics = self.analytics()
            return {
                "questions": [self.question_to_dict(question) for question in self.questions],
                "panelists": PANELISTS,
                "analytics": analytics,
            }

    @staticmethod
    def answer_to_dict(answer: Answer) -> dict[str, object]:
        return {
            "id": answer.id,
            "role": answer.role,
            "author": answer.author,
            "text": answer.text,
            "created_at": answer.created_at,
            "context_question_id": answer.context_question_id,
        }

    def question_to_dict(self, question: Question) -> dict[str, object]:
        return {
            "id": question.id,
            "text": question.text,
            "author": question.author,
            "votes": question.votes,
            "created_at": question.created_at,
            "keywords": self._question_keywords(question),
            "answers": [self.answer_to_dict(answer) for answer in question.answers],
            "has_panelist_answer": any(answer.role == "panelist" for answer in question.answers),
            "has_ai_answer": any(answer.role == "ai" for answer in question.answers),
        }

    def reset(self) -> None:
        with self._lock:
            self.questions.clear()
