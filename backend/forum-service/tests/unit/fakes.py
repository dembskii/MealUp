from __future__ import annotations

from typing import Any, Callable


_SENTINEL = object()


class FakeResult:
    def __init__(
        self,
        *,
        first: Any = _SENTINEL,
        all_values: list[Any] | None = None,
        scalar: Any = _SENTINEL,
    ) -> None:
        self._first = first
        self._all_values = list(all_values or [])
        self._scalar = scalar

    def first(self) -> Any:
        if self._first is not _SENTINEL:
            return self._first
        if self._all_values:
            return self._all_values[0]
        return None

    def all(self) -> list[Any]:
        return list(self._all_values)

    def scalar(self) -> Any:
        if self._scalar is not _SENTINEL:
            return self._scalar
        return self.first()


class FakeAsyncSession:
    def __init__(
        self,
        *,
        exec_plan: list[Any] | None = None,
        commit_plan: list[Any] | None = None,
    ) -> None:
        self.exec_plan = list(exec_plan or [])
        self.commit_plan = list(commit_plan or [])
        self.exec_calls: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.refreshed: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    async def exec(self, statement: Any, *args: Any, **kwargs: Any) -> FakeResult:
        self.exec_calls.append((statement, args, kwargs))

        if not self.exec_plan:
            return FakeResult(all_values=[])

        next_item = self.exec_plan.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        if callable(next_item):
            value = next_item(statement, *args, **kwargs)
            if isinstance(value, Exception):
                raise value
            return value
        return next_item

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def delete(self, obj: Any) -> None:
        self.deleted.append(obj)

    async def refresh(self, obj: Any) -> None:
        self.refreshed.append(obj)

    async def commit(self) -> None:
        self.commits += 1
        if self.commit_plan:
            next_item = self.commit_plan.pop(0)
            if isinstance(next_item, Exception):
                raise next_item

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeHttpResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeHttpClient:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def __aenter__(self) -> "FakeHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def get(self, url: str, **kwargs: Any) -> Any:
        self.calls.append((url, kwargs))
        if self._error is not None:
            raise self._error
        return self._response


def build_http_client_factory(response: Any = None, error: Exception | None = None) -> Callable[..., FakeHttpClient]:
    def _factory(*args: Any, **kwargs: Any) -> FakeHttpClient:
        return FakeHttpClient(response=response, error=error)

    return _factory
