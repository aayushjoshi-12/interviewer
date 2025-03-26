import os

import fitz
import psycopg
from langchain_community.document_loaders import WebBaseLoader
from langgraph.checkpoint.postgres.base import BasePostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def parse_pdf(file: __file__) -> str:
    pdf_docs = fitz.open(file, filetype="pdf")
    text = " ".join(page.get_text("text") for page in pdf_docs)
    return text


def parse_link(link: str) -> str:
    docs = WebBaseLoader(link).load()
    text = " ".join(doc.page_content for doc in docs)
    return text


async def get_checkpointer() -> BasePostgresSaver:
    conn = await psycopg.AsyncConnection.connect(
        os.environ.get("POSTGRES_DB_URL"), autocommit=True
    )
    checkpointer = AsyncPostgresSaver(conn)
    await checkpointer.setup()

    return checkpointer
