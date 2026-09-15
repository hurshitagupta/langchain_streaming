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

