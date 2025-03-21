from typing import List

from fastapi import UploadFile
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt
from utils import parse_link, parse_pdf

from core.runnables import (
    coding_question_assessment,
    experience_interviewer,
    generate_coding_question,
    job_description_parser,
    resume_breaker,
)
from schemas.llm_responses import Experience, ExperienceInterviewScore, Project


class Interview(MessagesState):
    job_description: str
    resume: UploadFile | str
    experiences: List[Experience]
    projects: List[Project]
    skills: List[str]
    coding_interview_score: int
    experience_interview_score: int


async def parser_node(state: Interview):
    # TODO: figure out how to get the resume
    resume = state["resume"]
    if isinstance(resume, UploadFile):
        resume_file = resume.file
        resume = parse_pdf(resume_file)

    job_description = state["job_description"]
    if job_description.startswith("https://"):
        job_description = parse_link(job_description)

    parsed_resume = await resume_breaker.ainvoke({"resume": resume})
    parsed_job_description = await job_description_parser.ainvoke(
        {"job_description": job_description}
    )
    return {
        "experiences": parsed_resume.experiences,
        "projects": parsed_resume.projects,
        "skills": parsed_resume.skills,
        "job_description": parsed_job_description.job_description,
    }


async def coding_interviewer_node(state: Interview):
    skills = ", ".join(skill for skill in state["skills"])
    coding_questions = await generate_coding_question.ainvoke({"skills": skills})
    questions = coding_questions.questions
    total_score = 10
    for question in questions:
        answer = interrupt(value=question)
        score = await coding_question_assessment.ainvoke(
            {"question": question, "response": answer}
        )
        total_score += score.score
    return {
        "coding_interview_score": total_score // len(questions),
    }


async def experience_interviewer_node(state: Interview):
    response = await experience_interviewer.ainvoke(
        {"experience": state["experiences"], "projects": state["projects"]}
    )
    if isinstance(response, ExperienceInterviewScore):
        return {"experience_interview_score": response.score}
    return Command(
        update={"messages": [{"role": "ai", "content": response.response}]},
        goto="candidate_node",
    )


def candidate_node(state: Interview):
    answer = interrupt("Answer the question. \n")
    return Command(
        update={"messages": [{"role": "human", "content": answer}]},
        goto="experience_interviewer_node",
    )


def should_end(state: Interview):
    if "experience_interview_score" in state and state["experience_interview_score"]:
        return END
    else:
        return "candidate_node"


def get_interview_agent() -> CompiledStateGraph:
    # TODO: take the the checkpointer as an argument
    workflow = StateGraph(Interview)

    workflow.add_node("parser_node", parser_node)
    workflow.add_node("coding_interviewer_node", coding_interviewer_node)
    workflow.add_node("experience_interviewer_node", experience_interviewer_node)
    workflow.add_node("candidate_node", candidate_node)

    workflow.add_edge(START, "parser_node")
    workflow.add_edge("parser_node", "coding_interviewer_node")
    workflow.add_edge("coding_interviewer_node", "experience_interviewer_node")
    workflow.add_edge("candidate_node", "experience_interviewer_node")
    workflow.add_conditional_edges(
        "experience_interviewer_node", should_end, ["candidate_node", END]
    )

    return workflow.compile(checkpointer=MemorySaver())
