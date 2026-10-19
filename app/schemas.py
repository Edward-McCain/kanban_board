import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Priority


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    return value or None


class ColumnCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=80)
    tone: str = Field(default="slate", pattern="^(slate|amber|violet|green)$")


class ColumnUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=80)


class MemberCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    role: str = Field(default="", max_length=40)
    avatar: str = Field(default="anya.jpg", max_length=80)


class TagCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=40)
    tone: str = Field(default="slate", pattern="^(slate|amber|violet|green|rose|blue)$")


class CardCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    column_id: uuid.UUID
    title: str = Field(min_length=1, max_length=160)
    note: str | None = Field(default=None, max_length=500)
    priority: Priority = Priority.MEDIUM
    due_on: date | None = None
    member_ids: list[uuid.UUID] = Field(default_factory=list)
    tag_ids: list[uuid.UUID] = Field(default_factory=list)

    def cleaned_note(self) -> str | None:
        return _blank(self.note)


class CardUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=160)
    note: str | None = Field(default=None, max_length=500)
    priority: Priority | None = None
    due_on: date | None = None
    member_ids: list[uuid.UUID] | None = None
    tag_ids: list[uuid.UUID] | None = None


class CardMove(BaseModel):
    column_id: uuid.UUID
    position: int = Field(ge=0)


class SubtaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=160)


class SubtaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=160)
    done: bool | None = None


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: str
    avatar: str


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    tone: str


class SubtaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    done: bool
    position: int


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    column_id: uuid.UUID
    title: str
    note: str | None
    priority: Priority
    due_on: date | None
    position: int
    created_at: datetime
    members: list[MemberOut]
    tags: list[TagOut]
    subtasks: list[SubtaskOut]


class ColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    tone: str
    position: int
    cards: list[CardOut]


class BoardOut(BaseModel):
    columns: list[ColumnOut]
    members: list[MemberOut]
    tags: list[TagOut]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
