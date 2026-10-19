import os
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command

os.environ.setdefault(
    "DATABASE_URL",
    f"postgresql+psycopg://{os.environ.get('USER', 'polotno')}@127.0.0.1:5432/polotno",
)
os.environ["SEED_BOARD"] = "0"

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def empty_board() -> Iterator[None]:
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE subtasks, card_members, card_tags, "
                "cards, board_columns, members, tags CASCADE"
            )
        )
    engine.dispose()
    yield


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
