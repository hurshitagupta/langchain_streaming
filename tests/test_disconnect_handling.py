import pytest

import disconnect_handling.disconnect_handling as dh


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeStream:
    def __init__(self):
        self.chunks = [
            "Hello ",
            "from ",
            "LangChain."
        ]
        self.index = 0
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.chunks):
            raise StopAsyncIteration

        chunk = self.chunks[self.index]
        self.index += 1

        return chunk

    async def aclose(self):
        self.closed = True


class FakeChain:
    def __init__(self):
        self.stream = FakeStream()

    def astream(self, data):
        return self.stream


class ConnectedRequest:
    async def is_disconnected(self):
        return False


class DisconnectedRequest:
    async def is_disconnected(self):
        return True


@pytest.mark.anyio
async def test_stream_success(monkeypatch):
    fake_chain = FakeChain()

    monkeypatch.setattr(dh,"chain",fake_chain)

    request = ConnectedRequest()

    events = []

    async for event in dh.generate_stream(request,"LangChain"):
        events.append(event)

    output = "".join(events)

    assert '"delta": "Hello "' in output
    assert '"delta": "from "' in output
    assert '"delta": "LangChain."' in output


@pytest.mark.anyio
async def test_disconnect_cancels_generation(monkeypatch,capsys,):
    fake_chain = FakeChain()

    monkeypatch.setattr(dh,"chain",fake_chain)

    request = DisconnectedRequest()

    events = []

    async for event in dh.generate_stream( request,"LangChain"):
        events.append(event)

    captured = capsys.readouterr().out

    assert events == []

    assert (
        "Client disconnected. "
        "Cancelling generation."
    ) in captured

    assert fake_chain.stream.closed is True


@pytest.mark.anyio
async def test_invalid_topic():
    request = ConnectedRequest()

    with pytest.raises(ValueError,match="Topic cannot be empty"):
        async for _ in dh.generate_stream(request,""):
            pass