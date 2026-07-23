"""Request-scoped context shared by middleware and logging."""

from contextvars import ContextVar, Token

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


def bind_request_id(request_id: str) -> Token[str | None]:
    """Bind a request ID and return the token needed to restore prior context."""
    return request_id_context.set(request_id)


def get_request_id() -> str | None:
    """Return the current request ID, if a request has bound one."""
    return request_id_context.get()


def reset_request_id(token: Token[str | None]) -> None:
    """Restore the request context that existed before binding."""
    request_id_context.reset(token)
