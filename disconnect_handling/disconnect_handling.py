import asyncio
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter


load_dotenv()

MAX_TOPIC_LENGTH = 200
MAX_CHUNKS = 1000


def validate_topic(topic: str) -> str:
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError("Token budget rejected: topic is too long.")

    return topic.strip()


def validate_chunk(chunk: str) -> str:
    if not isinstance(chunk, str):
        raise ValueError("Invalid model output quarantined.")

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
    "Explain {topic} in about 150 words using simple language."
)


chain = (prompt | model | StrOutputParser())

app = FastAPI()

async def generate_stream(request: Request, topic: str):
    topic = validate_topic(topic)

    chunk_count = 0
    stream = chain.astream({"topic": topic})

    try:
        async for chunk in stream:

            # Case 1: FastAPI reports that client disconnected
            if await request.is_disconnected():
                print(
                    "Client disconnected. "
                    "Cancelling generation."
                )

                if hasattr(stream, "aclose"):
                    await stream.aclose()

                return

            chunk = validate_chunk(chunk)

            if not chunk:
                continue

            chunk_count += 1

            if chunk_count > MAX_CHUNKS:
                print(
                    "Chunk limit reached. "
                    "Generation stopped."
                )

                yield (
                    "event: error\n"
                    'data: {"error": '
                    '"Chunk limit reached."}\n\n'
                )

                return

            data = {"delta": chunk}

            yield (f"data: {json.dumps(data)}\n\n")

    # Case 2: Uvicorn cancels the streaming task
    except asyncio.CancelledError:
        print(
            "Client disconnected. "
            "Cancelling generation."
        )

        if hasattr(stream, "aclose"):
            await stream.aclose()

        raise

    except Exception as exc:
        print(
            f"Streaming error: "
            f"{type(exc).__name__}"
        )

        error_data = {"error": type(exc).__name__}

        yield (
            "event: error\n"
            f"data: {json.dumps(error_data)}\n\n"
        )

    finally:
        print("Generation finished.")


@app.get("/stream")
async def stream(
    request: Request,
    topic: str = Query(
        default="LangChain streaming"
    ),
):
    return StreamingResponse(
        generate_stream(request, topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )