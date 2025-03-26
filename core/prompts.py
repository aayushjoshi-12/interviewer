from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


job_description_parser_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a job description parser. Your task is to parse the job description "
            "from the provided text below",
        ),
        ("system", "<job_description>\n{job_description}\n</job_description>"),
    ]
)


resume_breaker_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a resume parser. Your task is to breakdown the resume provided "
            "below into three sections: experiences, projects, and skills.",
        ),
        ("system", "<resume>\n{resume}\n</resume>"),
    ]
)

generate_coding_question_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a coding interviewer. Your task is to generate exactly 2 technical "
            "programming/coding questions based on the skills mentioned below."
        ),
        ("system", "<skills>\n{skills}\n</skills>"),
    ]
)

coding_question_assessment_promt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a coding interviewer. Your task is to assess the candidate's "
            "response by a score between 1 to 10 where 1 is very bad and 10 is perfect "
            "answer. Here is the question: \n{question}",
        ),
        ("human", "{response}"),
    ]
)

expereince_interviewer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an highly experienced interviewer at a tech company and your task is to take "
            "interviews of new candidates for the provided job description (if any is provided). You "
            "can ask questions about the candidate's previous work experiences. If you think that you "
            "need to ask a follow up question, you can ask that as well or else you can move on to the "
            "next question. If you feel you have asked enough questions (5 questions are sufficient but"
            " if you feel more are necessary go for it) and think you should end the interview give the "
            "score to candidate using Experience Interview Score schema. No need to extend you conversati"
            "on. Ask only relevant questions.",
        ),
        ("system", "<job_description>\n{job_description}\n</job_description>"),
        ("system", "<experience>\n{experience}\n</experience>"),
        ("system", "<projects>\n{projects}\n</projects>"),
        # MessagesPlaceholder("chat_history"),
    ]
)