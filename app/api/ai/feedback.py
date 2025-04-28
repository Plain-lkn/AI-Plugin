from fastapi import APIRouter
from app.core.ai_feedback import generate_feedback
from app.crud.feedback_data import process_pdf, create_subject, get_pass_subject, save_subject, format_docs
from langchain_openai import OpenAIEmbeddings
from app.schemas.feedback import Feedback

router = APIRouter()

@router.post("/feedback")
async def feedback(feedback: Feedback):
    docs = process_pdf(feedback.pdf_url)
    embeddings = OpenAIEmbeddings()
    subject = create_subject(docs, embeddings)
    pass_context = get_pass_subject(feedback.user_id)
    query = "문서에 대해 설명해줘"

    res = generate_feedback(pass_context, subject.as_retriever() | format_docs, query)
    save_subject(subject, feedback.user_id, embeddings)
    
    return res