import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter


load_dotenv()

MAX_TOPIC_LENGTH = 200
MAX_CHUNKS = 1000


def validate_topic(topic: str) -> str:
    """Validate the input topic."""

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError(
            "Token budget rejected: topic is too long."
        )

    return topic.strip()


def validate_chunk(chunk: str) -> str:
    """Validate model output before sending it to the client."""

    if not isinstance(chunk, str):
        raise ValueError(
            "Invalid model output quarantined."
        )

    return chunk


model = ChatOpenRouter(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0,
    timeout=30_000,
    max_retries=3,
)


prompt = ChatPromptTemplate.from_template(
    "Explain {topic} in about 60 words using simple language."
)


chain = (prompt| model| StrOutputParser())


app = FastAPI()


async def generate_stream(topic: str):
    """Generate model output and send it as SSE events."""

    chunk_count = 0

    try:
        # Validate input before calling the model
        topic = validate_topic(topic)

        async for chunk in chain.astream({"topic": topic}):

            # Validate output before sending it
            chunk = validate_chunk(chunk)

            # Ignore empty chunks
            if not chunk:
                continue

            # Count only meaningful chunks
            chunk_count += 1

            # Step/chunk limit guardrail
            if chunk_count > MAX_CHUNKS:
                error_data = {
                    "error": "Chunk limit reached."
                }

                yield (
                    "event: error\n"
                    f"data: {json.dumps(error_data)}\n\n"
                )
                return

            data = {
                "delta": chunk
            }

            # Send the chunk using SSE format
            yield (
                f"data: {json.dumps(data)}\n\n"
            )

    except Exception as exc:
        error_data = {
            "error": type(exc).__name__
        }

        # Errors are sent inside the stream
        yield (
            "event: error\n"
            f"data: {json.dumps(error_data)}\n\n"
        )

    finally:
        done_data = {
            "done": True
        }

        # Always tell the client that the stream has ended
        yield (
            "event: done\n"
            f"data: {json.dumps(done_data)}\n\n"
        )


@app.get("/stream")
async def stream(
    topic: str = Query(default="LangChain streaming")
):
    """SSE endpoint."""

    return StreamingResponse(
        generate_stream(topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )