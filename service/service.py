from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from core.agent import get_interview_agent
from schemas.schema import StreamInput, UserInput  # TODO: use __init__.py for import

# use lifespan if you need to init db or other stuff
app = FastAPI()
router = APIRouter()


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


def _parse_input(user_input: UserInput) -> tuple[dict[str, Any], UUID]:
    thread_id = user_input.thread_id or str(uuid4())

    configurable = {
        "thread_id": thread_id,
        # "model": user_input.model # TODO: when you have the getter method for the model
    }

    if user_input.agent_config:
        if overlap := configurable.keys() & user_input.agent_config.keys():
            raise HTTPException(
                status_code=422,
                detail=f"agent_config contains reserved keys: {overlap}",
            )
        configurable.update(user_input.agent_config)

    kwargs = {
        "input": Command(resume=user_input.message),
        "config": RunnableConfig(
            configurable=configurable,
        ),
    }
    return kwargs


async def message_generator(kwargs) -> AsyncGenerator[str, None]:
    """
    Generate a stream of messages from the agent.

    This is the workhorse method for the /stream endpoint.
    """
    agent: CompiledStateGraph = get_interview_agent()

    # Process streamed events from the graph and yield messages over the SSE stream.
    async for event in agent.astream(**kwargs):
        if not event:
            continue

        new_messages = []
        pass


@router.post(
    "/start", response_class=StreamingResponse, responses=_sse_response_example()
)
async def start(StartInput):
    thread_id = StartInput.thread_id or str(uuid4())
    kwargs = {
        "input": {
            "job_description": StartInput.job_description,
            "resume": StartInput.resume,
        },
        "config": RunnableConfig(
            configurable={"thread_id": thread_id},
        ),
    }
    return StreamingResponse(message_generator(kwargs), media_type="text/event-stream")


@router.post(
    "/stream", response_class=StreamingResponse, responses=_sse_response_example()
)
async def stream(user_input: StreamInput):
    kwargs = _parse_input(user_input)
    return StreamingResponse(message_generator(kwargs), media_type="text/event-stream")
