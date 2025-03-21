from langchain_community.document_loaders import WebBaseLoader
import fitz


def parse_pdf(file: __file__) -> str:
    pdf_docs = fitz.open(file, filetype="pdf")
    text = " ".join(page.get_text("text") for page in pdf_docs)
    return text

def parse_link(link: str) -> str:
    docs = WebBaseLoader(link).load()
    text = " ".join(doc.page_content for doc in docs)
    return text

# TODO: parse job description
# put it in the same node as the resume parser node 