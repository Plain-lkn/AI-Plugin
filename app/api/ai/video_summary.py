from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import os
import tempfile
from ai_textbook import VideoSummaryPDFGenerator

router = APIRouter()

@router.post("/generate-video-summary")
async def generate_video_summary(video: UploadFile = File(...)):
    try:
        # Save uploaded video to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            content = await video.read()
            temp_video.write(content)
            temp_video_path = temp_video.name
        
        # Generate PDF
        generator = VideoSummaryPDFGenerator()
        pdf_bytes, pdf_filename = generator.generate_pdf(temp_video_path)
        
        # Clean up temp file
        os.unlink(temp_video_path)
        
        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={pdf_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        # Clean up temp file in case of error
        if 'temp_video_path' in locals():
            os.unlink(temp_video_path)
        raise HTTPException(status_code=500, detail=str(e))