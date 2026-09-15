import asyncio
import os
import time

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter


load_dotenv()

MAX_TOPIC_LENGTH = 200
MAX_CHUNKS = 1000
NUMBER_OF_RUNS = 10


def validate_topic(topic: str) -> str:
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError(
            "Token budget rejected: topic is too long."
        )

    return topic.strip()


def validate_chunk(chunk: str) -> str:
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
    "Explain {topic} in about 40 words using simple language."
)


chain =  prompt | model | StrOutputParser()


async def measure_run(topic: str):
    topic = validate_topic(topic)

    start_time = time.perf_counter()

    first_token_time = None
    chunk_count = 0
    full_response = ""

    try:
        async for chunk in chain.astream({"topic": topic}):

            chunk = validate_chunk(chunk)

            if not chunk:
                continue

            chunk_count += 1

            if chunk_count > MAX_CHUNKS:
                raise RuntimeError(
                    "Chunk limit reached."
                )

            if first_token_time is None:
                first_token_time = (
                    time.perf_counter() - start_time
                )

            full_response += chunk

    except TimeoutError:
        print("Request timed out.")
        raise

    if first_token_time is None:
        raise ValueError(
            "Invalid model output quarantined: empty response."
        )

    total_time = (
        time.perf_counter() - start_time
    )

    return {
        "ttft": first_token_time,
        "total_time": total_time,
        "chunks": chunk_count,
        "response": full_response,
    }


async def run_report(topic: str):
    print(f"TTFT Report for: {topic}")
    print(f"Runs: {NUMBER_OF_RUNS}\n")

    results = []

    for run_number in range(
        1,
        NUMBER_OF_RUNS + 1
    ):
        result = await measure_run(topic)

        results.append(result)

        print(
            f"Run {run_number:02d} | "
            f"TTFT: {result['ttft']:.2f}s | "
            f"Total: {result['total_time']:.2f}s"
        )

    average_ttft = sum(result["ttft"] for result in results) / len(results)

    average_total = sum(result["total_time"] for result in results) / len(results)

    print("\n--- Summary ---")

    print(
        f"Average TTFT: "
        f"{average_ttft:.2f}s"
    )

    print(
        f"Average Total Time: "
        f"{average_total:.2f}s"
    )

    return results


if __name__ == "__main__":
    asyncio.run(
        run_report("LangChain streaming")
    )