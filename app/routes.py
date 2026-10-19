import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import BoardColumn, Card, Member, Tag
from app.schemas import (
    BoardOut,
    CardCreate,
    CardMove,
    CardOut,
    CardUpdate,
    ColumnCreate,
    ColumnOut,
    ColumnUpdate,
    ErrorResponse,
    MemberCreate,
    MemberOut,
    SubtaskCreate,
    SubtaskUpdate,
    TagCreate,
    TagOut,
)
from app.service import (
    add_subtask,
    create_card,
    create_column,
    create_member,
    create_tag,
    delete_card,
    delete_column,
    delete_subtask,
    load_board,
    load_members,
    load_tags,
    move_card,
    rename_column,
    update_card,
    update_subtask,
)

router = APIRouter(prefix="/api", tags=["доска"])
SessionDep = Annotated[Session, Depends(get_session)]
ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


def present_column(column: BoardColumn) -> ColumnOut:
    return ColumnOut.model_validate(column)


def present_card(card: Card) -> CardOut:
    return CardOut.model_validate(card)


def present_member(member: Member) -> MemberOut:
    return MemberOut.model_validate(member)


def present_tag(tag: Tag) -> TagOut:
    return TagOut.model_validate(tag)


@router.get("/health")
def health(session: SessionDep) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/board", response_model=BoardOut)
def read_board(session: SessionDep) -> BoardOut:
    return BoardOut(
        columns=[present_column(column) for column in load_board(session)],
        members=[present_member(member) for member in load_members(session)],
        tags=[present_tag(tag) for tag in load_tags(session)],
    )


@router.post("/members", status_code=201, response_model=MemberOut, responses=ERRORS)
def post_member(payload: MemberCreate, session: SessionDep) -> MemberOut:
    return present_member(create_member(session, payload))


@router.post("/tags", status_code=201, response_model=TagOut, responses=ERRORS)
def post_tag(payload: TagCreate, session: SessionDep) -> TagOut:
    return present_tag(create_tag(session, payload))


@router.post("/columns", status_code=201, response_model=ColumnOut, responses=ERRORS)
def post_column(payload: ColumnCreate, session: SessionDep) -> ColumnOut:
    return present_column(create_column(session, payload))


@router.patch("/columns/{column_id}", response_model=ColumnOut, responses=ERRORS)
def patch_column(column_id: uuid.UUID, payload: ColumnUpdate, session: SessionDep) -> ColumnOut:
    return present_column(rename_column(session, column_id, payload.title))


@router.delete("/columns/{column_id}", status_code=204, responses=ERRORS)
def remove_column(column_id: uuid.UUID, session: SessionDep) -> None:
    delete_column(session, column_id)


@router.post("/cards", status_code=201, response_model=CardOut, responses=ERRORS)
def post_card(payload: CardCreate, session: SessionDep) -> CardOut:
    return present_card(create_card(session, payload))


@router.patch("/cards/{card_id}", response_model=CardOut, responses=ERRORS)
def patch_card(card_id: uuid.UUID, payload: CardUpdate, session: SessionDep) -> CardOut:
    return present_card(update_card(session, card_id, payload))


@router.post("/cards/{card_id}/move", response_model=CardOut, responses=ERRORS)
def post_move(card_id: uuid.UUID, payload: CardMove, session: SessionDep) -> CardOut:
    return present_card(move_card(session, card_id, payload.column_id, payload.position))


@router.delete("/cards/{card_id}", status_code=204, responses=ERRORS)
def remove_card(card_id: uuid.UUID, session: SessionDep) -> None:
    delete_card(session, card_id)


@router.post("/cards/{card_id}/subtasks", response_model=CardOut, responses=ERRORS)
def post_subtask(card_id: uuid.UUID, payload: SubtaskCreate, session: SessionDep) -> CardOut:
    return present_card(add_subtask(session, card_id, payload))


@router.patch("/subtasks/{subtask_id}", response_model=CardOut, responses=ERRORS)
def patch_subtask(subtask_id: uuid.UUID, payload: SubtaskUpdate, session: SessionDep) -> CardOut:
    return present_card(update_subtask(session, subtask_id, payload))


@router.delete("/subtasks/{subtask_id}", response_model=CardOut, responses=ERRORS)
def remove_subtask(subtask_id: uuid.UUID, session: SessionDep) -> CardOut:
    return present_card(delete_subtask(session, subtask_id))
