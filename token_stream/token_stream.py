import os
import time

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter


load_dotenv()

MAX_STEPS = 100
MAX_TOPIC_LENGTH = 200


def validate_topic(topic: str) -> str:
    """Validate input before sending it to the model."""

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError("Token budget rejected: topic is too long.")

    return topic.strip()


def validate_chunk(chunk: str) -> str:
    """Validate streamed model output."""

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
    "Explain {topic} in about 80 words using simple language."
)


chain = prompt | model | StrOutputParser()


def stream_response(topic: str) -> str:
    topic = validate_topic(topic)

    print(f"Streaming response for: {topic}\n")

    full_response = ""
    step_count = 0
    start_time = time.perf_counter()

    try:
        for chunk in chain.stream({"topic": topic}):
            step_count += 1

            if step_count > MAX_STEPS:
                print("\nStep limit reached. Streaming stopped.")
                break

            chunk = validate_chunk(chunk)

            print(chunk, end="", flush=True)
            full_response += chunk

    except TimeoutError:
        print("\nRequest timed out.")
        raise

    except Exception as exc:
        print(f"\nStreaming failed: {type(exc).__name__}: {exc}")
        raise

    total_time = time.perf_counter() - start_time

    if not full_response.strip():
        raise ValueError("Invalid model output quarantined: empty response.")

    print(f"\n\nStream completed in {total_time:.2f} seconds.")
    print(f"Chunks received: {step_count}")

    return full_response


if __name__ == "__main__":
    stream_response("LangChain streaming")