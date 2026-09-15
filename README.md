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
