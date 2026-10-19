from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

FIELD_MESSAGE = {
    "title": "Нужно название.",
    "note": "Описание длиннее 500 знаков.",
    "name": "Нужно имя.",
    "priority": "Приоритет: низкий, средний, высокий или срочный.",
    "member_ids": "Не вижу участника.",
    "tag_ids": "Не вижу метку.",
    "due_on": "Дату запишите как 2026-10-24.",
    "position": "Позиция — целое число от нуля.",
    "column_id": "Не вижу колонку.",
}


class NotFound(Exception):
    message: str

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class Conflict(Exception):
    message: str

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def validation_message(exc: RequestValidationError) -> str:
    error = exc.errors()[0]
    loc = error.get("loc", ())
    field = ""
    if isinstance(loc, tuple | list):
        for part in reversed(loc):
            if isinstance(part, str) and part not in {"body", "query", "path"}:
                field = part
                break
    return FIELD_MESSAGE.get(field, "Запрос не разобрать.")


def _payload(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def register(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def not_found(_request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content=_payload("not_found", exc.message))

    @app.exception_handler(Conflict)
    async def conflict(_request: Request, exc: Conflict) -> JSONResponse:
        return JSONResponse(status_code=409, content=_payload("conflict", exc.message))

    @app.exception_handler(RequestValidationError)
    async def invalid(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_payload("validation", validation_message(exc)),
        )
