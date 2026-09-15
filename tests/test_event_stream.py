import pytest

import event_stream.event_stream as es


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeChunk:
    def __init__(self, content):
        self.content = content


class FakeEventChain:
    async def astream_events(self, topic, version="v2"):
        yield {
            "event": "on_chain_start",
            "name": "retriever",
            "data": {},
        }

        yield {
            "event": "on_chain_end",
            "name": "retriever",
            "data": {},
        }

        yield {
            "event": "on_chat_model_start",
            "name": "model",
            "data": {},
        }

        yield {
            "event": "on_chat_model_stream",
            "name": "model",
            "data": {
                "chunk": FakeChunk("Streaming works.")
            },
        }

        yield {
            "event": "on_chat_model_end",
            "name": "model",
            "data": {},
        }


@pytest.mark.anyio
async def test_event_stream_success(monkeypatch, capsys):
    monkeypatch.setattr(es,"answer_chain",FakeEventChain())

    await es.stream_events("LangChain")

    output = capsys.readouterr().out

    assert "[Retriever started]" in output
    assert "[Retriever finished]" in output
    assert "[Model started]" in output
    assert "Streaming works." in output
    assert "[Model finished]" in output


@pytest.mark.anyio
async def test_event_stream_failure():
    with pytest.raises(ValueError,match="Topic cannot be empty"):
        await es.stream_events("")