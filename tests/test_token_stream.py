import pytest

import token_stream.token_stream as ts


class FakeChain:
    def stream(self, data):
        yield "Streaming "
        yield "works "
        yield "correctly."


def test_stream_success(monkeypatch):
    monkeypatch.setattr(ts, "chain", FakeChain())

    result = ts.stream_response("LangChain")

    assert result == "Streaming works correctly."


def test_empty_topic_failure():
    with pytest.raises(ValueError, match="Topic cannot be empty"):
        ts.stream_response("")