from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, Field, StringConstraints, model_validator


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=128)


class PasswordIn(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class UserIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=200, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=12, max_length=128)
    role: Literal['admin', 'teacher', 'student']


class ClassIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    grade: int = Field(ge=1, le=10)
    teacher_ids: list[int] = Field(default_factory=list, max_length=30)
    student_ids: list[int] = Field(default_factory=list, max_length=100)


class AttendanceIn(BaseModel):
    day: date
    absent_ids: list[int] = Field(default_factory=list, max_length=100)
    correction_reason: str = Field(default='', max_length=500)
    confirmed: bool
    expected_version: str | None = None


class MaterialIn(BaseModel):
    class_id: int
    subject_id: int
    title: str = Field(min_length=3, max_length=160)
    content: str = Field(min_length=30, max_length=60000)
    approved: bool = False


class HomeworkIn(BaseModel):
    class_id: int
    subject_id: int
    title: str = Field(min_length=3, max_length=160)
    instructions: str = Field(min_length=5, max_length=10000)
    due_date: date


class SubmitIn(BaseModel):
    answer: str = Field(min_length=1, max_length=20000)


class ReviewIn(BaseModel):
    status: Literal['complete', 'needs_revision']
    feedback: str = Field(max_length=2000)


class QuestionOut(BaseModel):
    kind: Literal['mcq', 'short_answer']
    question: str = Field(min_length=8, max_length=1000)
    options: list[str] = Field(default_factory=list, max_length=4)
    answer: str = Field(min_length=1, max_length=1500)
    explanation: str = Field(min_length=5, max_length=2000)
    source_quote: str = Field(min_length=10, max_length=2000)
    topic: str = Field(min_length=2, max_length=100)

    @model_validator(mode='after')
    def valid_answer(self):
        if self.kind == 'mcq' and (len(self.options) != 4 or len(set(self.options)) != 4 or self.answer not in self.options):
            raise ValueError('MCQs need four distinct options and an answer matching one option')
        if self.kind == 'short_answer' and self.options:
            raise ValueError('Short answers must not contain options')
        return self


class CardOut(BaseModel):
    front: str = Field(min_length=3, max_length=500)
    back: str = Field(min_length=3, max_length=1500)


class LearningPack(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    summary: str = Field(min_length=20, max_length=5000)
    questions: list[QuestionOut] = Field(min_length=6, max_length=12)
    flashcards: list[CardOut] = Field(min_length=2, max_length=12)

    @model_validator(mode='after')
    def no_duplicates(self):
        normalized = [q.question.casefold().strip() for q in self.questions]
        if len(normalized) != len(set(normalized)):
            raise ValueError('Duplicate questions')
        if sum(q.kind == 'mcq' for q in self.questions) < 5:
            raise ValueError('At least five MCQs required for the daily challenge')
        if not any(q.kind == 'short_answer' for q in self.questions):
            raise ValueError('At least one short-answer question is required')
        fronts = [' '.join(c.front.casefold().split()) for c in self.flashcards]
        if len(fronts) != len(set(fronts)):
            raise ValueError('Duplicate flashcard fronts')
        return self


class GenerateIn(BaseModel):
    material_id: int
    language: Literal['en', 'hi'] = 'en'


class TutorIn(GenerateIn):
    question: str = Field(min_length=3, max_length=1000)


class TutorOut(BaseModel):
    answer: str = Field(min_length=10, max_length=4000)
    source_quote: str = Field(max_length=2000)
    follow_up: str = Field(min_length=3, max_length=500)
    insufficient_context: bool


class AttemptIn(BaseModel):
    mode: Literal['daily', 'class'] = 'class'
    answers: dict[int, str]


class AnnouncementIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=5, max_length=3000)
