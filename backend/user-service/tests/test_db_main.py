import pytest

import src.db.main as db_main


@pytest.mark.asyncio
async def test_get_session_yields_session(monkeypatch: pytest.MonkeyPatch):
    sentinel_session = object()

    class DummySessionContext:
        async def __aenter__(self):
            return sentinel_session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummySessionmaker:
        def __call__(self):
            return DummySessionContext()

    def _fake_sessionmaker(**_kwargs):
        return DummySessionmaker()

    monkeypatch.setattr(db_main, "sessionmaker", _fake_sessionmaker)

    generator = db_main.get_session()
    yielded = await generator.__anext__()
    assert yielded is sentinel_session

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()
