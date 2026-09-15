from fastapi.testclient import TestClient

import sse_endpoint.sse_endpoint as sse


class FakeChain:
    async def astream(self, data):
        yield "LangChain "
        yield "streaming "
        yield "works."


def test_sse_success(monkeypatch):
    monkeypatch.setattr(
        sse,
        "chain",
        FakeChain()
    )

    client = TestClient(sse.app)

    response = client.get(
        "/stream?topic=LangChain"
    )

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )

    assert response.headers["cache-control"] == "no-cache"

    assert response.headers["x-accel-buffering"] == "no"

    assert '"delta": "LangChain "' in response.text
    assert '"delta": "streaming "' in response.text
    assert '"done": true' in response.text


def test_sse_failure():
    client = TestClient(sse.app)

    long_topic = "a" * 201

    response = client.get(
        f"/stream?topic={long_topic}"
    )

    assert response.status_code == 200
    assert "ValueError" in response.text
    assert '"done": true' in response.text