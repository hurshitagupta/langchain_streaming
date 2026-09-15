import pytest

import ttft_report.ttft_report as ttft


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeChain:
    async def astream(self, data):
        yield ""
        yield "Streaming "
        yield "works."


@pytest.mark.anyio
async def test_measure_run_success(monkeypatch):
    monkeypatch.setattr(ttft,"chain",FakeChain())

    result = await ttft.measure_run(
        "LangChain"
    )

    assert result["ttft"] >= 0
    assert result["total_time"] >= result["ttft"]

    assert result["chunks"] == 2

    assert result["response"] == ("Streaming works.")


@pytest.mark.anyio
async def test_measure_run_failure():
    with pytest.raises(ValueError,match="Topic cannot be empty"):
        await ttft.measure_run("")