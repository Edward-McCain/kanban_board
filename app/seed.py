from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BoardColumn, Card, Member, Priority, Subtask, Tag


def seed_if_empty(session: Session) -> None:
    existing = session.scalar(select(func.count()).select_from(BoardColumn))
    if existing:
        return
    today = date.today()
    people = {
        name: Member(name=name, role=role, avatar=avatar)
        for name, role, avatar in (
            ("Аня Соколова", "Дизайн", "anya.jpg"),
            ("Марк Левин", "Фронтенд", "mark.jpg"),
            ("Лена Орлова", "Бэкенд", "lena.jpg"),
            ("Илья Ким", "Тестирование", "ilya.jpg"),
            ("Соня Беридзе", "Продакт", "sonya.jpg"),
        )
    }
    labels = {
        name: Tag(name=name, tone=tone)
        for name, tone in (
            ("Фронтенд", "blue"),
            ("API", "violet"),
            ("Авторизация", "rose"),
            ("Интерфейс", "amber"),
            ("База", "green"),
        )
    }
    session.add_all([*people.values(), *labels.values()])
    columns = [
        BoardColumn(title="К выполнению", tone="slate", position=0),
        BoardColumn(title="В работе", tone="amber", position=1),
        BoardColumn(title="На проверке", tone="violet", position=2),
        BoardColumn(title="Готово", tone="green", position=3),
    ]
    session.add_all(columns)
    session.flush()
    backlog, doing, review, done = columns
    cards = [
        _card(
            backlog,
            0,
            "Нарисовать пустые состояния",
            "Что видит человек, если в колонке ещё нет задач.",
            Priority.LOW,
            today + timedelta(days=5),
            [people["Аня Соколова"]],
            [labels["Интерфейс"]],
            [("Текст для пустой колонки", False), ("Кнопка новой задачи", False)],
        ),
        _card(
            backlog,
            1,
            "Описать контракт входа",
            "Почта, пароль и какой ответ получает клиент.",
            Priority.MEDIUM,
            today + timedelta(days=4),
            [people["Соня Беридзе"], people["Лена Орлова"]],
            [labels["Авторизация"], labels["API"]],
            [("Поля формы", False), ("Коды ошибок", False)],
        ),
        _card(
            backlog,
            2,
            "Собрать страницу профиля",
            "Имя, роль и смена пароля. Без лишних полей.",
            Priority.LOW,
            today + timedelta(days=6),
            [people["Марк Левин"]],
            [labels["Фронтенд"]],
            [],
        ),
        _card(
            doing,
            0,
            "Сделать вход по почте",
            "Форма на клиенте, сессия на сервере, понятная ошибка.",
            Priority.HIGH,
            today + timedelta(days=1),
            [people["Лена Орлова"], people["Марк Левин"]],
            [labels["Авторизация"], labels["Фронтенд"]],
            [("Форма входа", True), ("Сессия", False), ("Текст ошибки", False)],
        ),
        _card(
            doing,
            1,
            "Починить перенос карточки на телефоне",
            "Жест срывается, если палец чуть уехал в сторону.",
            Priority.URGENT,
            today,
            [people["Марк Левин"]],
            [labels["Фронтенд"]],
            [("Порог до начала переноса", False), ("Отмена жеста", False)],
        ),
        _card(
            doing,
            2,
            "Не отдавать чужую карточку",
            "Запрос с чужим id должен отвечать 404, а не чужими данными.",
            Priority.MEDIUM,
            today + timedelta(days=2),
            [people["Лена Орлова"]],
            [labels["API"]],
            [("Проверка id", True), ("Ответ 404", False)],
        ),
        _card(
            review,
            0,
            "Проверить регистрацию на телефоне",
            "Кнопка создания аккаунта уезжает под клавиатуру.",
            Priority.HIGH,
            today,
            [people["Илья Ким"]],
            [labels["Авторизация"]],
            [("iPhone", True), ("Android", False)],
        ),
        _card(
            review,
            1,
            "Ревью миграции пользователей",
            "Нужны индекс почты и рабочий откат.",
            Priority.MEDIUM,
            today + timedelta(days=1),
            [people["Лена Орлова"]],
            [labels["База"]],
            [("Индекс почты", True), ("Откат миграции", False)],
        ),
        _card(
            done,
            0,
            "Поднять базу и миграции",
            "Postgres поднимается, схема накатывается с пустой базы.",
            Priority.LOW,
            today - timedelta(days=1),
            [people["Лена Орлова"]],
            [labels["База"]],
            [("Compose для Postgres", True), ("Первая миграция", True)],
        ),
        _card(
            done,
            1,
            "Собрать колонки и карточки",
            "Доска открывается, карточку можно создать и перенести.",
            Priority.LOW,
            today - timedelta(days=2),
            [people["Марк Левин"], people["Аня Соколова"]],
            [labels["Фронтенд"], labels["Интерфейс"]],
            [("Колонки", True), ("Карточка", True), ("Перенос", True)],
        ),
    ]
    session.add_all(cards)
    session.flush()


def _card(
    column: BoardColumn,
    position: int,
    title: str,
    note: str,
    priority: Priority,
    due_on: date,
    members: list[Member],
    tags: list[Tag],
    steps: list[tuple[str, bool]],
) -> Card:
    card = Card(
        column_id=column.id,
        title=title,
        note=note,
        priority=priority.value,
        due_on=due_on,
        position=position,
        members=members,
        tags=tags,
    )
    card.subtasks = [
        Subtask(title=step_title, done=done, position=index)
        for index, (step_title, done) in enumerate(steps)
    ]
    return card
