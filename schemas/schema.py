from fastapi import UploadFile
from pydantic import BaseModel, Field


class StartInput(BaseModel):
    """Input for starting a new conversation."""

    job_description: str = Field(
        description="Job description of the job you want to prepare for. Can be a URL or plain text.",
        examples=[
            "https://example.com/job-description",
            "Software Engineer at Google...",
        ],
    )
    resume: UploadFile | str = Field(description="Resume file in PDF format or as plain text")
    thread_id: str | None = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    # TODO: add more formats support like .docx, etc or str


class UserInput(BaseModel):
    """Basic user input for the agent."""

    message: str = Field(
        description="User input to the agent.",
        examples=["What is the weather in Tokyo?"],
    )
    thread_id: str | None = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    # TODO: implement all model enum to alloq user to select any available model
    # model: SerializeAsAny[AllModelEnum] | None = Field(
    #     title="Model",
    #     description="LLM Model to use for the agent.",
    #     default=OpenAIModelName.GPT_4O_MINI,
    #     examples=[OpenAIModelName.GPT_4O_MINI, AnthropicModelName.HAIKU_35],
    # )


class StreamInput(UserInput):
    """User input for streaming the agent's response."""

    stream_tokens: bool = Field(
        description="Whether to stream LLM tokens to the client.",
        default=True,
    )
