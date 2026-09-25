from pydantic import BaseModel, Field, field_validator


class QuestionCreate(BaseModel):
    text: str = Field(min_length=3, max_length=280)
    author: str = Field(default="Asistente anónimo", min_length=2, max_length=60)

    @field_validator("text", "author")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("El texto no puede estar vacío")
        return cleaned


class PanelistAnswerCreate(BaseModel):
    panelist: str = Field(min_length=2, max_length=60)
    text: str = Field(min_length=3, max_length=1200)

    @field_validator("panelist", "text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("El texto no puede estar vacío")
        return cleaned
