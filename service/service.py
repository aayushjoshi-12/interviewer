import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import AnyMessage, ChatMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from core.agent import get_interview_agent
from schemas import ChatHistory, ChatHistoryInput, StartInput, StateInput, UserInput
from service.utils import (
    convert_message_content_to_string,
    remove_tool_calls,
)

app = FastAPI()
router = APIRouter()

logger = logging.getLogger(__name__)


def _sse_response_example() -> dict[int, Any]:
    return {
        status.HTTP_200_OK: {
            "description": "Server Sent Event Response",
            "content": {
                "text/event-stream": {
                    "example": "data: {'type': 'token', 'content': 'Hello'}\n\ndata: {'type': 'token', 'content': ' World'}\n\ndata: [DONE]\n\n",
                    "schema": {"type": "string"},
                }
            },
        }
    }


async def message_generator(kwargs) -> AsyncGenerator[str, None]:
    """
    Generate a stream of messages from the agent.

    This is the workhorse method for the /stream endpoint.
    """
    logger.info(
        f"Starting message generation with thread_id: {kwargs.get('config', {}).get('configurable', {}).get('thread_id')}"
    )
    agent: CompiledStateGraph = await get_interview_agent()

    try:
        async for event in agent.astream_events(**kwargs, version="v2"):
            if not event:
                continue

            logger.debug(f"Received event: {event['event']}")
            new_messages = []
            if event["event"] == "on_chain_end" and any(
                t.startswith("graph:step:") for t in event.get("tags", [])
            ):
                logger.debug(
                    f"Processing chain end event with tags: {event.get('tags', [])}"
                )
                if isinstance(event["data"]["output"], Command):
                    new_messages = event["data"]["output"].update.get("messages", [])
                elif "messages" in event["data"]["output"]:
                    new_messages = event["data"]["output"]["messages"]

            for message in new_messages:
                logger.debug(f"Yielding new message of role: {message.type}")
                yield f"data: {json.dumps({'type': 'message', 'content': message.model_dump()})}\n\n"

            if event["event"] == "on_chat_model_stream":
                content = remove_tool_calls(event["data"]["chunk"].content)
                if content:
                    logger.debug(f"Streaming token: {content[:20]}...")
                    yield f"data: {json.dumps({'type': 'token', 'content': convert_message_content_to_string(content)})}\n\n"
                continue

        logger.info("Message generation completed successfully")
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error in message generation: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred during message generation'})}\n\n"
        yield "data: [DONE]\n\n"


@router.post(
    "/start", response_class=StreamingResponse, responses=_sse_response_example()
)
async def start(start_input: StartInput) -> StreamingResponse:
    thread_id = start_input.thread_id
    logger.info(f"Starting new interview session with thread_id: {thread_id}")
    logger.debug(
        f"Job description length: {len(start_input.job_description)}, Resume length: {len(start_input.resume)}"
    )

    kwargs = {
        "input": {
            "job_description": start_input.job_description,
            "resume": start_input.resume,
        },
        "config": RunnableConfig(configurable={"thread_id": thread_id}),
    }
    logger.info(f"Initiating streaming response for thread: {thread_id}")
    return StreamingResponse(message_generator(kwargs), media_type="text/event-stream")


@router.post(
    "/stream", response_class=StreamingResponse, responses=_sse_response_example()
)
async def stream(user_input: UserInput) -> StreamingResponse:
    logger.info(f"Received user message for thread: {user_input.thread_id}")
    logger.debug(f"User message: {user_input.message[:50]}...")

    kwargs = {
        "input": Command(resume=user_input.message),
        "config": RunnableConfig(configurable={"thread_id": user_input.thread_id}),
    }
    logger.info(f"Continuing conversation stream for thread: {user_input.thread_id}")
    return StreamingResponse(message_generator(kwargs), media_type="text/event-stream")


@router.post("/history")
async def history(history_input: ChatHistoryInput) -> ChatHistory:
    logger.info(f"Retrieving chat history for thread: {history_input.thread_id}")

    agent: CompiledStateGraph = await get_interview_agent()
    try:
        state_snapshot = await agent.aget_state(
            config=RunnableConfig(configurable={"thread_id": history_input.thread_id})
        )
        messages: list[AnyMessage] = state_snapshot.values["messages"]
        chat_messages: list[ChatMessage] = [m for m in messages]
        logger.info(
            f"Successfully retrieved {len(chat_messages)} messages for thread: {history_input.thread_id}"
        )
        return ChatHistory(messages=chat_messages)
    except Exception as e:
        logger.error(
            f"Failed to retrieve chat history for thread {history_input.thread_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error")


@router.post("/state")
async def state(state_input: StateInput):
    logger.info(f"Ending conversation for thread: {state_input.thread_id}")

    agent: CompiledStateGraph = await get_interview_agent()
    try:
        state_snapshot = await agent.aget_state(
            config=RunnableConfig(configurable={"thread_id": state_input.thread_id})
        )
        logger.info(
            f"Successfully ended conversation for thread: {state_input.thread_id}"
        )
        return {"state_snapshot": f"{json.dumps(state_snapshot.values)}"}
    except Exception as e:
        logger.error(
            f"Failed to end conversation for thread {state_input.thread_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error")


# TODO: give description to the endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint called")
    return {"status": "ok"}


app.include_router(router)
