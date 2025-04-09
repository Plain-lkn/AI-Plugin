from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os
from ai_textbook import VideoSummaryPDFGenerator
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat import get_response
import tempfile

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

@app.post("/generate-video-summary")
async def generate_video_summary(video: UploadFile = File(...)):
    try:
        # Save uploaded video to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            content = await video.read()
            temp_video.write(content)
            temp_video_path = temp_video.name
        
        # Generate PDF
        generator = VideoSummaryPDFGenerator()
        pdf_bytes = generator.generate_pdf(temp_video_path)
        
        # Clean up temp file
        os.unlink(temp_video_path)
        
        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=video_summary.pdf"}
        )
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_video_path' in locals():
            os.unlink(temp_video_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}