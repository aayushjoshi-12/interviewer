import operator
from typing import Annotated, List

from fastapi import UploadFile
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from core.runnables import (
    coding_question_assessment,
    experience_interviewer,
    generate_coding_question,
    job_description_parser,
    resume_breaker,
)
from core.utils import get_checkpointer, parse_link, parse_pdf
from schemas.llm_responses import Experience, ExperienceInterviewScore, Project


class Interview(MessagesState):
    job_description: str = None
    resume: str | UploadFile = None  # TODO: fix this error
    experiences: List[Experience] = []
    projects: List[Project] = []
    skills: List[str] = []
    coding_interview_running: bool = False
    coding_questions: List[str] = None
    current_question_index: int = None
    coding_scores: Annotated[List[int], operator.add] = []
    coding_interview_score: int = None
    experience_interview_score: int = None


async def parser_node(state: Interview):
    # TODO: give llm the entire ability to parse the resume and break it down
    # in whatever parts he feels suitable and then make decisions accordingly
    resume = state["resume"]

    if isinstance(resume, UploadFile):
        resume_content = await parse_pdf(resume)
    else:
        resume_content = resume

    job_description = state["job_description"]
    if job_description.startswith("https://"):
        job_description = parse_link(job_description)

    parsed_resume = await resume_breaker.ainvoke({"resume": resume_content})
    parsed_job_description = await job_description_parser.ainvoke(
        {"job_description": job_description}
    )
    return {
        "experiences": parsed_resume.experiences,
        "projects": parsed_resume.projects,
        "skills": parsed_resume.skills,
        "job_description": parsed_job_description.job_description,
        "coding_interview_running": False,
    }


async def coding_interviewer_node(state: Interview):
    if not state["coding_interview_running"]:
        skills = ", ".join(skill for skill in state["skills"])
        coding_questions = await generate_coding_question.ainvoke({"skills": skills})
        return {
            "messages": [AIMessage(content=coding_questions.questions[0])],
            "coding_questions": coding_questions.questions,
            "current_question_index": 0,
            "coding_scores": [],
            "coding_interview_running": True,
        }

    question = state["coding_questions"][state["current_question_index"]]
    last_message = state["messages"][-1].content

    score = await coding_question_assessment.ainvoke(
        {"question": question, "response": last_message}
    )

    next_index = state["current_question_index"] + 1

    if next_index < len(state["coding_questions"]):
        return {
            "messages": [AIMessage(content=state["coding_questions"][next_index])],
            "coding_scores": [score.score],
            "current_question_index": next_index,
        }
    else:
        total_score = sum(state["coding_scores"])
        return {
            "coding_interview_score": total_score // len(state["coding_questions"]),
        }


async def experience_interviewer_node(state: Interview):
    response = await experience_interviewer.ainvoke(
        {
            "job_description": state["job_description"],
            "experience": state["experiences"],
            "projects": state["projects"],
            # "chat_history": state["messages"], #TODO: dumpt it as a json into a system message if this doesn't works
        }
    )
    if isinstance(response, ExperienceInterviewScore):
        # TODO: some other logic this ain't working
        # maybe because rn we are not passing history
        # check with history once
        return {"experience_interview_score": response.score}
    return {"messages": [AIMessage(content=response.response)]}


def candidate_node(state: Interview):
    answer = interrupt("")
    # TODO: make it so that we can end convo here directly
    return {"messages": [HumanMessage(content=answer)]}


def should_end_coding(state: Interview):
    if (
        "coding_interview_score" in state
        and state["coding_interview_score"] is not None
    ):
        return "experience_interviewer_node"
    else:
        return "candidate_node"


def should_end_experience(state: Interview):
    if (
        "experience_interview_score" in state
        and state["experience_interview_score"] is not None
    ):
        return END
    else:
        return "candidate_node"


def should_go_to_coding(state: Interview):
    if state["coding_interview_running"]:
        return "coding_interviewer_node"
    else:
        return "experience_interviewer_node"


async def get_interview_agent() -> CompiledStateGraph:
    workflow = StateGraph(Interview)

    workflow.add_node("parser_node", parser_node)
    workflow.add_node("coding_interviewer_node", coding_interviewer_node)
    workflow.add_node("experience_interviewer_node", experience_interviewer_node)
    workflow.add_node("candidate_node", candidate_node)

    workflow.add_edge(START, "parser_node")
    workflow.add_edge("parser_node", "coding_interviewer_node")

    workflow.add_conditional_edges(
        "coding_interviewer_node",
        should_end_coding,
        ["experience_interviewer_node", "candidate_node"],
    )
    workflow.add_conditional_edges(
        "experience_interviewer_node", should_end_experience, ["candidate_node", END]
    )
    workflow.add_conditional_edges(
        "candidate_node",
        should_go_to_coding,
        ["coding_interviewer_node", "experience_interviewer_node"],
    )

    checkpointer = await get_checkpointer()

    return workflow.compile(checkpointer=checkpointer)
