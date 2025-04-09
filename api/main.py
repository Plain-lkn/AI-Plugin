from student_data import get_student_submission, get_student_summary
from feedback_utils import get_related_feedbacks, generate_feedback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
from ai_textbook import VideoSummaryPDFGenerator

app = FastAPI()

# Create a directory for temporary files if it doesn't exist
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.post("/generate-video-summary")
async def generate_video_summary(video: UploadFile = File(...)):
    try:
        # Save uploaded video to temporary file
        temp_video_path = os.path.join(TEMP_DIR, video.filename)
        with open(temp_video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Generate PDF summary
        generator = VideoSummaryPDFGenerator()
        pdf_path = generator.generate_pdf(temp_video_path)
        
        # Return the PDF file
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=os.path.basename(pdf_path)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def main():
    student_id = "A123"
    class_name = "대학 영어 글쓰기"  # or 동적으로 설정

    student_text = get_student_submission(student_id)
    student_summary = get_student_summary(student_id)
    related_feedbacks = get_related_feedbacks(student_id, student_text)

    feedback = generate_feedback(student_summary, related_feedbacks, student_text, class_name)

    print("\n📋 생성된 피드백:\n")
    print(feedback)


if __name__ == "__main__":
    main()
