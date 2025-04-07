from fastapi import FastAPI
from pydantic import BaseModel
from chat import get_response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    사용자의 메시지를 받아 AI의 응답을 반환합니다.
    """
    response = get_response(request.message)
    return ChatResponse(response=response)

@app.get("/")
async def root():
    """
    서버 상태 확인용 엔드포인트
    """
    return {"status": "ok", "message": "Chat API is running"}