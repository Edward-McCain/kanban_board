import httpx
import pytest

pytestmark = pytest.mark.anyio


async def make_column(client: httpx.AsyncClient, title: str) -> dict[str, object]:
    response = await client.post("/api/columns", json={"title": title})
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, dict)
    return body


async def make_card(
    client: httpx.AsyncClient,
    column_id: object,
    title: str,
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {"column_id": column_id, "title": title, **extra}
    response = await client.post("/api/cards", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body, dict)
    return body


async def test_board_starts_empty(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/board")
    assert response.status_code == 200
    assert response.json() == {"columns": [], "members": [], "tags": []}


async def test_create_rename_and_reject_empty_title(client: httpx.AsyncClient) -> None:
    column = await make_column(client, "  Бэклог  ")
    assert column["title"] == "Бэклог"
    renamed = await client.patch(f"/api/columns/{column['id']}", json={"title": "Идеи"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Идеи"
    invalid = await client.post("/api/columns", json={"title": "   "})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["message"] == "Нужно название."


async def test_move_between_columns_keeps_order(client: httpx.AsyncClient) -> None:
    backlog = await make_column(client, "Бэклог")
    doing = await make_column(client, "В работе")
    first = await make_card(client, backlog["id"], "Сверстать профиль", priority="low")
    second = await make_card(client, backlog["id"], "Сделать вход", priority="high")
    parked = await make_card(client, doing["id"], "Проверить регистрацию")

    moved = await client.post(
        f"/api/cards/{second['id']}/move",
        json={"column_id": doing["id"], "position": 0},
    )
    assert moved.status_code == 200
    assert moved.json()["position"] == 0
    assert moved.json()["column_id"] == doing["id"]

    board = (await client.get("/api/board")).json()
    columns = {item["title"]: item for item in board["columns"]}
    assert [card["title"] for card in columns["Бэклог"]["cards"]] == ["Сверстать профиль"]
    assert [card["title"] for card in columns["В работе"]["cards"]] == [
        "Сделать вход",
        "Проверить регистрацию",
    ]
    assert columns["Бэклог"]["cards"][0]["id"] == first["id"]
    assert columns["В работе"]["cards"][1]["id"] == parked["id"]


async def test_reorder_inside_column(client: httpx.AsyncClient) -> None:
    column = await make_column(client, "Бэклог")
    first = await make_card(client, column["id"], "Первая")
    await make_card(client, column["id"], "Вторая")
    moved = await client.post(
        f"/api/cards/{first['id']}/move",
        json={"column_id": column["id"], "position": 1},
    )
    assert moved.status_code == 200
    board = (await client.get("/api/board")).json()
    titles = [card["title"] for card in board["columns"][0]["cards"]]
    assert titles == ["Вторая", "Первая"]


async def test_cannot_delete_column_with_cards(client: httpx.AsyncClient) -> None:
    column = await make_column(client, "Бэклог")
    card = await make_card(client, column["id"], "Одна")
    denied = await client.delete(f"/api/columns/{column['id']}")
    assert denied.status_code == 409
    removed = await client.delete(f"/api/cards/{card['id']}")
    assert removed.status_code == 204
    assert (await client.delete(f"/api/columns/{column['id']}")).status_code == 204


async def test_patch_clears_note_and_missing_card(client: httpx.AsyncClient) -> None:
    column = await make_column(client, "Бэклог")
    card = await make_card(client, column["id"], "Вход", note="  форма и сессия  ")
    assert card["note"] == "форма и сессия"
    cleared = await client.patch(
        f"/api/cards/{card['id']}",
        json={"note": None, "priority": "urgent"},
    )
    assert cleared.status_code == 200
    assert cleared.json()["note"] is None
    assert cleared.json()["priority"] == "urgent"
    missing = await client.patch(
        "/api/cards/00000000-0000-0000-0000-000000000000",
        json={"title": "Нет"},
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


async def test_people_tags_and_subtasks(client: httpx.AsyncClient) -> None:
    column = await make_column(client, "Бэклог")
    member = await client.post(
        "/api/members",
        json={"name": "Аня Соколова", "role": "Дизайн", "avatar": "anya.jpg"},
    )
    tag = await client.post("/api/tags", json={"name": "Интерфейс", "tone": "amber"})
    assert member.status_code == 201
    assert tag.status_code == 201
    member_body = member.json()
    tag_body = tag.json()
    assert isinstance(member_body, dict)
    assert isinstance(tag_body, dict)
    card = await make_card(
        client,
        column["id"],
        "Пустое состояние",
        member_ids=[member_body["id"]],
        tag_ids=[tag_body["id"]],
    )
    members = card["members"]
    tags = card["tags"]
    assert isinstance(members, list)
    assert isinstance(tags, list)
    assert isinstance(members[0], dict)
    assert isinstance(tags[0], dict)
    assert members[0]["name"] == "Аня Соколова"
    assert tags[0]["name"] == "Интерфейс"
    with_step = await client.post(
        f"/api/cards/{card['id']}/subtasks",
        json={"title": "Серый фон"},
    )
    assert with_step.status_code == 200
    step = with_step.json()["subtasks"][0]
    done = await client.patch(f"/api/subtasks/{step['id']}", json={"done": True})
    assert done.json()["subtasks"][0]["done"] is True
    cleared = await client.delete(f"/api/subtasks/{step['id']}")
    assert cleared.status_code == 200
    assert cleared.json()["subtasks"] == []
