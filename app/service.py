import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.errors import Conflict, NotFound
from app.models import BoardColumn, Card, Member, Subtask, Tag
from app.schemas import (
    CardCreate,
    CardUpdate,
    ColumnCreate,
    MemberCreate,
    SubtaskCreate,
    SubtaskUpdate,
    TagCreate,
)


def load_board(session: Session) -> list[BoardColumn]:
    return list(
        session.scalars(
            select(BoardColumn)
            .options(
                selectinload(BoardColumn.cards).selectinload(Card.members),
                selectinload(BoardColumn.cards).selectinload(Card.tags),
                selectinload(BoardColumn.cards).selectinload(Card.subtasks),
            )
            .order_by(BoardColumn.position)
        ).all()
    )


def load_members(session: Session) -> list[Member]:
    return list(session.scalars(select(Member).order_by(Member.name)).all())


def load_tags(session: Session) -> list[Tag]:
    return list(session.scalars(select(Tag).order_by(Tag.name)).all())


def create_member(session: Session, payload: MemberCreate) -> Member:
    member = Member(name=payload.name, role=payload.role, avatar=payload.avatar)
    session.add(member)
    session.flush()
    return member


def create_tag(session: Session, payload: TagCreate) -> Tag:
    tag = Tag(name=payload.name, tone=payload.tone)
    session.add(tag)
    session.flush()
    return tag


def create_column(session: Session, payload: ColumnCreate) -> BoardColumn:
    last = session.scalar(select(BoardColumn.position).order_by(BoardColumn.position.desc()))
    column = BoardColumn(
        title=payload.title,
        tone=payload.tone,
        position=0 if last is None else last + 1,
    )
    session.add(column)
    session.flush()
    return column


def rename_column(session: Session, column_id: uuid.UUID, title: str) -> BoardColumn:
    column = session.get(BoardColumn, column_id)
    if column is None:
        raise NotFound("Колонки нет.")
    column.title = title
    session.flush()
    return column


def delete_column(session: Session, column_id: uuid.UUID) -> None:
    column = session.get(BoardColumn, column_id)
    if column is None:
        raise NotFound("Колонки нет.")
    taken = session.scalar(select(Card.id).where(Card.column_id == column_id).limit(1))
    if taken is not None:
        raise Conflict("В колонке ещё есть карточки. Сначала перенесите их.")
    session.delete(column)
    _renumber_columns(session)


def create_card(session: Session, payload: CardCreate) -> Card:
    column = session.get(BoardColumn, payload.column_id)
    if column is None:
        raise NotFound("Колонки нет.")
    last = session.scalar(
        select(Card.position).where(Card.column_id == column.id).order_by(Card.position.desc())
    )
    card = Card(
        column_id=column.id,
        title=payload.title,
        note=payload.cleaned_note(),
        priority=payload.priority.value,
        due_on=payload.due_on,
        position=0 if last is None else last + 1,
    )
    session.add(card)
    session.flush()
    _set_members(session, card, payload.member_ids)
    _set_tags(session, card, payload.tag_ids)
    return _full_card(session, card.id)


def update_card(session: Session, card_id: uuid.UUID, payload: CardUpdate) -> Card:
    card = session.get(Card, card_id)
    if card is None:
        raise NotFound("Карточки нет.")
    fields = payload.model_fields_set
    if "title" in fields and payload.title is not None:
        card.title = payload.title
    if "note" in fields:
        card.note = payload.note or None
    if "priority" in fields and payload.priority is not None:
        card.priority = payload.priority.value
    if "due_on" in fields:
        card.due_on = payload.due_on
    if "member_ids" in fields and payload.member_ids is not None:
        _set_members(session, card, payload.member_ids)
    if "tag_ids" in fields and payload.tag_ids is not None:
        _set_tags(session, card, payload.tag_ids)
    session.flush()
    return _full_card(session, card.id)


def delete_card(session: Session, card_id: uuid.UUID) -> None:
    card = session.get(Card, card_id)
    if card is None:
        raise NotFound("Карточки нет.")
    column_id = card.column_id
    session.delete(card)
    session.flush()
    _renumber(session, column_id)


def move_card(session: Session, card_id: uuid.UUID, column_id: uuid.UUID, position: int) -> Card:
    # Два переноса сразу не должны перемешать position:
    # строки обеих колонок держим до конца транзакции.
    card = session.get(Card, card_id, with_for_update=True)
    if card is None:
        raise NotFound("Карточки нет.")
    if session.get(BoardColumn, column_id) is None:
        raise NotFound("Колонки нет.")
    source_id = card.column_id
    locked = list(
        session.scalars(
            select(Card)
            .where(Card.column_id.in_([source_id, column_id]))
            .order_by(Card.position, Card.id)
            .with_for_update()
        ).all()
    )
    source = [item for item in locked if item.column_id == source_id and item.id != card.id]
    target = (
        source
        if source_id == column_id
        else [item for item in locked if item.column_id == column_id and item.id != card.id]
    )
    index = max(0, min(position, len(target)))
    target.insert(index, card)
    card.column_id = column_id
    if source_id != column_id:
        _write_positions(source)
    _write_positions(target)
    session.flush()
    return _full_card(session, card.id)


def add_subtask(session: Session, card_id: uuid.UUID, payload: SubtaskCreate) -> Card:
    card = session.get(Card, card_id)
    if card is None:
        raise NotFound("Карточки нет.")
    last = session.scalar(
        select(Subtask.position).where(Subtask.card_id == card_id).order_by(Subtask.position.desc())
    )
    session.add(
        Subtask(
            card_id=card_id,
            title=payload.title,
            position=0 if last is None else last + 1,
        )
    )
    session.flush()
    return _full_card(session, card_id)


def update_subtask(session: Session, subtask_id: uuid.UUID, payload: SubtaskUpdate) -> Card:
    subtask = session.get(Subtask, subtask_id)
    if subtask is None:
        raise NotFound("Пункта нет.")
    fields = payload.model_fields_set
    if "title" in fields and payload.title is not None:
        subtask.title = payload.title
    if "done" in fields and payload.done is not None:
        subtask.done = payload.done
    session.flush()
    return _full_card(session, subtask.card_id)


def delete_subtask(session: Session, subtask_id: uuid.UUID) -> Card:
    subtask = session.get(Subtask, subtask_id)
    if subtask is None:
        raise NotFound("Пункта нет.")
    card_id = subtask.card_id
    session.delete(subtask)
    session.flush()
    rows = list(
        session.scalars(
            select(Subtask).where(Subtask.card_id == card_id).order_by(Subtask.position, Subtask.id)
        ).all()
    )
    for index, row in enumerate(rows):
        row.position = index
    session.flush()
    return _full_card(session, card_id)


def _set_members(session: Session, card: Card, member_ids: list[uuid.UUID]) -> None:
    card.members = _pick(session, Member, member_ids, "Участника нет.")


def _set_tags(session: Session, card: Card, tag_ids: list[uuid.UUID]) -> None:
    card.tags = _pick(session, Tag, tag_ids, "Метки нет.")


def _pick[T: (Member, Tag)](
    session: Session,
    model: type[T],
    wanted_ids: list[uuid.UUID],
    missing: str,
) -> list[T]:
    wanted = list(dict.fromkeys(wanted_ids))
    if not wanted:
        return []
    found = list(session.scalars(select(model).where(model.id.in_(wanted))).all())
    if len(found) != len(wanted):
        raise NotFound(missing)
    order = {item_id: index for index, item_id in enumerate(wanted)}
    found.sort(key=lambda item: order[item.id])
    return found


def _full_card(session: Session, card_id: uuid.UUID) -> Card:
    card = session.scalar(
        select(Card)
        .where(Card.id == card_id)
        .options(
            selectinload(Card.members),
            selectinload(Card.tags),
            selectinload(Card.subtasks),
        )
    )
    if card is None:
        raise NotFound("Карточки нет.")
    return card


def _renumber(session: Session, column_id: uuid.UUID) -> None:
    cards = list(
        session.scalars(
            select(Card).where(Card.column_id == column_id).order_by(Card.position, Card.id)
        ).all()
    )
    _write_positions(cards)


def _renumber_columns(session: Session) -> None:
    columns = list(session.scalars(select(BoardColumn).order_by(BoardColumn.position)).all())
    for index, column in enumerate(columns):
        column.position = index


def _write_positions(cards: list[Card]) -> None:
    for index, card in enumerate(cards):
        card.position = index
