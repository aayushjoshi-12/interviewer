from langchain_groq import ChatGroq

from core.prompts import (
    coding_question_assessment_promt,
    expereince_interviewer_prompt,
    generate_coding_question_prompt,
    job_description_parser_prompt,
    resume_breaker_prompt,
)
from schemas.llm_responses import (
    CodingInterviewScore,
    CodingQuestions,
    ExperienceInterviewQuestion,
    JobDescription,
    Resume,
)

# TODO: improve all prompts
# TODO: the model is going to get deprecated soon so look for alternates that perform well.
# TODO: rather than importing all the prompts create a getter function
llm = ChatGroq(model="mixtral-8x7b-32768")

resume_breaker = resume_breaker_prompt | llm.with_structured_output(Resume)

job_description_parser = job_description_parser_prompt | llm.with_structured_output(
    JobDescription
)

generate_coding_question = generate_coding_question_prompt | llm.with_structured_output(
    CodingQuestions
)

coding_question_assessment = (
    coding_question_assessment_promt | llm.with_structured_output(CodingInterviewScore)
)

experience_interviewer = expereince_interviewer_prompt | llm.with_structured_output(
    ExperienceInterviewQuestion
)
