from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_people"
down_revision: str | None = "0001_board"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "board_columns",
        sa.Column("tone", sa.String(length=16), nullable=False, server_default="slate"),
    )
    op.alter_column("board_columns", "tone", server_default=None)
    op.drop_column("cards", "owner")
    op.drop_constraint("card_priority", "cards", type_="check")
    op.create_check_constraint(
        "card_priority",
        "cards",
        "priority IN ('low', 'medium', 'high', 'urgent')",
    )
    op.create_table(
        "members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("avatar", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("tone", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "card_members",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("card_id", "member_id"),
    )
    op.create_table(
        "card_tags",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("card_id", "tag_id"),
    )
    op.create_table(
        "subtasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subtasks_card_id", "subtasks", ["card_id"])


def downgrade() -> None:
    op.drop_index("ix_subtasks_card_id", table_name="subtasks")
    op.drop_table("subtasks")
    op.drop_table("card_tags")
    op.drop_table("card_members")
    op.drop_table("tags")
    op.drop_table("members")
    op.drop_constraint("card_priority", "cards", type_="check")
    op.create_check_constraint(
        "card_priority",
        "cards",
        "priority IN ('low', 'medium', 'high')",
    )
    op.add_column("cards", sa.Column("owner", sa.String(length=40), nullable=True))
    op.drop_column("board_columns", "tone")
