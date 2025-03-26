from typing import List, Union

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Schema for a job description."""

    job_description: str = Field(description="The job description.")


class Experience(BaseModel):
    """Schema for an experience entry on resume."""

    title: str = Field(description="The title of the job.")
    description: str = Field(description="A description of the job.")


class Project(BaseModel):
    """Schema for a project entry on resume."""

    title: str = Field(description="The title of the project.")
    description: str = Field(description="A description of the project.")


class Resume(BaseModel):
    """Breakdown of a resume into experiences, projects, and skills."""

    experiences: List[Experience] = Field(
        description="The experiences listed on the resume."
    )
    projects: List[Project] = Field(description="The projects listed on the resume.")
    skills: List[str] = Field(description="The skills listed on the resume.")


class CodingQuestions(BaseModel):
    """Schema for a coding question."""

    questions: List[str] = Field(description="The list of technical coding questions.")


class CodingInterviewScore(BaseModel):
    """Schema for a coding interview score."""

    score: int = Field(description="The score of the candidate's response.")


class ExperienceInterviewScore(BaseModel):
    """Schema for an experience interview score."""

    score: int = Field(description="The score of the candidate's response.")


class ExperienceInterviewQuestion(BaseModel):
    """Schema for an experience interview."""

    response: Union[str, ExperienceInterviewScore] = Field(
        description=(
            "The question you want to ask. If you want to stop the conversation, "
            "provide the score to candidate's responses using the Experience "
            "Interview score schema."
        )
    )