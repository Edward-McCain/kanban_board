import os
import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Table, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(80))
    tone: Mapped[str] = mapped_column(String(16), default="slate")
    position: Mapped[int]
    cards: Mapped[list["Card"]] = relationship(
        back_populates="column",
        order_by="Card.position",
        cascade="all, delete-orphan",
    )


card_members = Table(
    "card_members",
    Base.metadata,
    Column("card_id", Uuid, ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    Column("member_id", Uuid, ForeignKey("members.id", ondelete="CASCADE"), primary_key=True),
)

card_tags = Table(
    "card_tags",
    Base.metadata,
    Column("card_id", Uuid, ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Uuid, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(40), default="")
    avatar: Mapped[str] = mapped_column(String(80))


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(40))
    tone: Mapped[str] = mapped_column(String(16), default="slate")


class Subtask(Base):
    __tablename__ = "subtasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160))
    done: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int]
    card: Mapped["Card"] = relationship(back_populates="subtasks")


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="card_priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    column_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("board_columns.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160))
    note: Mapped[str | None] = mapped_column(String(500))
    priority: Mapped[str] = mapped_column(String(16), default=Priority.MEDIUM.value)
    due_on: Mapped[date | None]
    position: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    column: Mapped[BoardColumn] = relationship(back_populates="cards")
    members: Mapped[list[Member]] = relationship(secondary=card_members)
    tags: Mapped[list[Tag]] = relationship(secondary=card_tags)
    subtasks: Mapped[list[Subtask]] = relationship(
        back_populates="card",
        order_by="Subtask.position",
        cascade="all, delete-orphan",
    )


def database_url() -> str:
    configured = os.environ.get("DATABASE_URL")
    if configured:
        return configured
    # Локально роль Postgres обычно совпадает с пользователем системы.
    # В Docker адрес всегда приходит снаружи.
    user = os.environ.get("USER", "polotno")
    return f"postgresql+psycopg://{user}@127.0.0.1:5432/polotno"
