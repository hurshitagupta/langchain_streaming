import asyncio
import os

from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openrouter import ChatOpenRouter


load_dotenv()

MAX_TOPIC_LENGTH = 200
MAX_STEPS = 10


def validate_topic(topic: str) -> str:
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError("Token budget rejected: topic is too long.")

    return topic.strip()


def retrieve_documents(topic: str):
    """Simple retriever step used for event streaming."""

    documents = [
        Document(
            page_content="Streaming sends model output in chunks as it is generated."
        ),
        Document(
            page_content="Time to first token measures how quickly the first output appears."
        ),
    ]

    return {
        "topic": topic,
        "context": "\n".join(doc.page_content for doc in documents),
    }


retriever = RunnableLambda(retrieve_documents).with_config({"run_name": "retriever"})


model = ChatOpenRouter(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0,
    timeout=30_000,
    max_retries=3,
)


prompt = ChatPromptTemplate.from_template(
    """
Use the following context to answer the question.

Context:
{context}

Question:
Explain {topic} in about 60 words using simple language.
"""
)


answer_chain = retriever | prompt | model | StrOutputParser()


async def stream_events(topic: str):
    topic = validate_topic(topic)

    event_count = 0
    step_count = 0

    print(f"Event stream for: {topic}\n")

    try:
        async for event in answer_chain.astream_events(
            topic,
            version="v2",
        ):
            event_count += 1

            event_type = event["event"]
            event_name = event.get("name", "")

            if event_type in ("on_chain_start", "on_chat_model_start"):
                step_count += 1

            if step_count > MAX_STEPS:
                print("\nStep limit reached. Streaming stopped.")
                break

            if event_name == "retriever":
                if event_type == "on_chain_start":
                    print("[Retriever started]")

                elif event_type == "on_chain_end":
                    print("[Retriever finished]")

            elif event_type == "on_chat_model_start":
                print("[Model started]")

            elif event_type == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content

                if not isinstance(chunk, str):
                    raise ValueError(
                        "Invalid model output quarantined."
                    )

                print(chunk, end="", flush=True)

            elif event_type == "on_chat_model_end":
                print("\n[Model finished]")

    except TimeoutError:
        print("\nRequest timed out.")
        raise

    except Exception as exc:
        print(f"\nEvent streaming failed: {type(exc).__name__}: {exc}")
        raise

    print(f"\nEvents processed: {event_count}")
    print(f"Execution steps: {step_count}")


if __name__ == "__main__":
    asyncio.run(stream_events("LangChain streaming"))