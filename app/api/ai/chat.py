from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.core.chat import get_response

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    사용자의 메시지를 받아 AI의 응답을 반환합니다.
    """
    response = get_response(request.message)
    return ChatResponse(response=response)