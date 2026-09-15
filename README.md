# LangChain Streaming — Topic 14

This project implements the hands-on assessment for **Topic 14 — Implement Streaming in Code**.

## Task 1 — Token Stream

Task 1 implements token streaming using LangChain's `.stream()` method. Instead of waiting for the complete model response, the output is displayed in the terminal as chunks are generated.

### Implementation

The streaming chain consists of:

```text
Prompt → Chat Model → StrOutputParser
```

The chain is executed using `.stream()` and each received chunk is immediately printed using:

```python
print(chunk, end="", flush=True)
```

This allows the response to appear progressively instead of waiting for the complete generation.

The streamed chunks are also combined into `full_response`, which is returned after streaming completes.

### Guardrails

The implementation includes the following safeguards:

* **Input validation** — empty topics are rejected before calling the model.
* **Input budget** — overly long topics are rejected.
* **Step limit** — the number of streamed chunks is capped.
* **Timeout** — model calls have a configured timeout.
* **Retry** — model retries are limited to a fixed number of attempts.
* **Output validation** — streamed chunks are validated before being returned to the caller.
* **Secret hygiene** — API credentials and model configuration are loaded from environment variables and are not stored directly in the source code.

### Run Task 1

From the project root:

```bash
uv run python -m token_stream.token_stream
```

The terminal displays the model response progressively as chunks are received and reports the total streaming time and number of chunks.

### Tests

Run the tests using:

```bash
uv run pytest tests/test_token_stream.py -v
```

### Task 1 Deliverables

* Token streaming implemented using `.stream()`.
* Real model output displayed progressively in the terminal.
* Input and output validation implemented.
* Required guardrails included in the implementation.
* Success and failure cases covered by automated tests.
* Runnable using a single documented command.

---

## Task 2 — Event Stream

Task 2 implements event streaming using LangChain's `astream_events()` method. Unlike normal token streaming, event streaming allows the application to observe what is happening at different stages of the chain.

### Implementation

A simple retrieval and generation pipeline is used:

```text
Retriever → Prompt → Chat Model → StrOutputParser
```

The retriever provides context about streaming, which is then passed to the prompt and model.

The chain is executed using:

```python
answer_chain.astream_events(topic, version="v2")
```

The implementation listens for relevant events and displays:

* Retriever started.
* Retriever finished.
* Model started.
* Model output as it is streamed.
* Model finished.

This allows an application or UI to show actual pipeline progress instead of only displaying a loading indicator.

### Events and Execution Steps

`astream_events()` can generate many low-level events during one chain execution, including individual model streaming events.

Because these events are not all separate execution steps, the step-limit guardrail counts major execution-start events rather than every streamed event.

### Guardrails

Task 2 includes:

* **Input validation** — empty topics are rejected.
* **Input budget** — excessively long topics are rejected.
* **Step limit** — major execution steps are capped without incorrectly counting individual streamed chunks as separate steps.
* **Timeout** — model calls use a configured timeout.
* **Retry** — model retries are limited.
* **Output validation** — streamed model chunks are validated before being displayed.
* **Secret hygiene** — API credentials and model configuration are loaded from environment variables.

### Run Task 2

From the project root:

```bash
uv run python -m event_stream.event_stream
```

### Tests

Run:

```bash
uv run pytest tests/test_event_stream.py -v
```

### Task 2 Deliverables

* Event streaming implemented using `astream_events()`.
* Retriever events surfaced.
* Model lifecycle events surfaced.
* Model output streamed progressively.
* Execution step limit implemented.
* Success and failure cases covered by automated tests.
* Runnable using a single documented command.

---

## Task 3 — SSE Endpoint

### Overview

Task 3 implements a Server-Sent Events (SSE) endpoint using FastAPI.

The LangChain response is generated asynchronously using `astream()` and each model chunk is sent to the client over HTTP as soon as it becomes available.

This extends the streaming implementation from Task 1 by exposing the streamed output through an actual HTTP endpoint.

### Implementation

The streaming flow is:

```text
Prompt → Chat Model → StrOutputParser → FastAPI → SSE Client
```

The endpoint is available at:

```text
GET /stream
```

The model response is streamed using:

```python
async for chunk in chain.astream({"topic": topic}):
```

### SSE Configuration

The endpoint uses FastAPI's `StreamingResponse` with:

```text
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
```

These headers allow the response to be streamed progressively instead of being buffered before reaching the client.

### Error Handling

If an error occurs after streaming has started, the error is returned inside the SSE stream:

```text
event: error
data: {"error": "ErrorType"}
```

A final `done` event is emitted when the stream ends.

This is important because once an HTTP streaming response has started, the application cannot rely on changing the HTTP status code to report a later streaming error.

### Guardrails

The task includes:

* Input validation for empty topics
* Input length/token-budget protection
* Model timeout configuration
* Retry configuration with capped attempts
* Output validation before chunks are returned
* Maximum meaningful chunk limit
* Secret hygiene using environment variables
* SSE error handling and final termination event

Empty model chunks are skipped and are not counted toward the chunk limit.

### Run Task 3

Start the FastAPI server:

```bash
uv run uvicorn sse_endpoint.sse_endpoint:app --reload
```

In another terminal, connect to the SSE endpoint:

```bash
curl.exe -N "http://127.0.0.1:8000/stream?topic=LangChain"
```

### Tests

Run the tests with:

```bash
uv run pytest tests/test_sse_endpoint.py -v
```

Expected result:

```text
test_sse_success PASSED
test_sse_failure PASSED

2 passed
```

### Task 3 Deliverables Completed

Task 3 demonstrates a working FastAPI SSE endpoint, asynchronous LangChain streaming, correct SSE headers, progressive HTTP delivery, error events, a final termination event, guardrails, and automated success/failure tests.

---

## Task 4 — TTFT Report

### Overview

Task 4 measures the performance of streaming by calculating **Time to First Token (TTFT)** and **total generation time** across 10 model runs.

TTFT measures how long the user waits before seeing the first visible part of the model response, while total time measures how long the complete response takes to generate.

### Implementation

The response is streamed asynchronously using:

```python
async for chunk in chain.astream({"topic": topic}):
```

A timer is started immediately before generation begins:

```python
start_time = time.perf_counter()
```

When the first non-empty chunk arrives, its arrival time is recorded:

```python
if first_token_time is None:
    first_token_time = (
        time.perf_counter() - start_time
    )
```

After the complete stream finishes, the total generation time is calculated.

Empty chunks are ignored so that TTFT represents the arrival of the **first visible model output**, rather than an empty provider event.

### 10-Run Report

The measurement is performed over 10 actual model runs:

```python
NUMBER_OF_RUNS = 10
```

### Guardrails

The task includes:

* Input validation for empty topics
* Input length/token-budget protection
* Model timeout configuration
* Retry configuration with capped attempts
* Output validation before accepting model chunks
* Maximum meaningful chunk limit
* Empty-response quarantine
* Secret hygiene using environment variables

Only non-empty model chunks are counted and used for TTFT measurement.

### Run Task 4

Run the TTFT report using:

```bash
uv run python -m ttft_report.ttft_report
```

### Tests

Run the tests using:

```bash
uv run pytest tests/test_ttft_report.py -v
```

### Task 4 Deliverables Completed

Task 4 demonstrates TTFT measurement, total generation-time measurement, 10-run performance reporting, average latency calculation, streaming output validation, guardrails, and automated success/failure tests.

The key measurement is **TTFT**, because it represents how quickly the user starts receiving visible output even when the complete model response takes longer to finish.

---

## Task 5 — Disconnect Handling

### Overview

Task 5 adds client disconnect handling to the streaming endpoint.

While the model is generating and streaming a response, the server checks whether the client is still connected. If the client disconnects, the generation is stopped so that the model does not continue producing output unnecessarily.

This extends the SSE implementation from Task 3 by adding cancellation handling.

### Implementation


The client connection is checked during streaming using:

```python
if await request.is_disconnected():
```

If a disconnect is detected, the application logs:

```text
Client disconnected. Cancelling generation.
```

The model stream is then closed using:

```python
if hasattr(stream, "aclose"):
    await stream.aclose()
```

and the generator returns so that no additional output is produced.

The implementation also handles `asyncio.CancelledError`, which may occur when the server cancels the streaming task after the client connection is closed.

### Guardrails

The task includes:

* Input validation for empty topics
* Input length/token-budget protection
* Model timeout configuration
* Retry configuration with capped attempts
* Output validation before sending model chunks
* Maximum meaningful chunk limit
* Client disconnect detection
* Async cancellation handling
* Model stream cleanup using `aclose()`
* Secret hygiene using environment variables

### Run Task 5

Start the disconnect-handling FastAPI server:

```bash
uv run uvicorn disconnect_handling.disconnect_handling:app --reload
```

In another terminal, connect to the endpoint:

```bash
curl.exe -N "http://127.0.0.1:8000/stream?topic=Explain%20LangChain%20streaming%20in%20detail"
```

The client can be disconnected while generation is running by pressing `Ctrl+C`.

The disconnect-handling logic then stops the generation instead of allowing unnecessary streaming work to continue.

### Tests

Run the tests using:

```bash
uv run pytest tests/test_disconnect_handling.py -v

```

## Task 5 Deliverables Completed

Task 5 demonstrates client disconnect detection, cancellation of an active model stream, cleanup of the asynchronous stream, cancellation logging, SSE streaming, guardrails, and automated success/failure testing.

This prevents the server from continuing unnecessary model generation after the client is no longer connected.

