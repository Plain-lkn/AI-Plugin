import whisper
import re
import json
import os
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from openai import OpenAI
from tempfile import NamedTemporaryFile
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# === 설정 ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLC_CX")

client = OpenAI(api_key=OPENAI_API_KEY)
model = whisper.load_model("base")
router = APIRouter()

# === 시간 포맷 변환 ===
def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# === GPT 요약 ===
def summarize_section(text):
    prompt = f"""
다음 내용을 기반으로 다음 정보를 생성해줘. 대상은 고등학생이야:

1. 제목 (한글로 간결하게)
2. 한 문장 요약
3. 2~3줄의 쉬운 설명

내용:
{text}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()
    lines = re.findall(r'\d+\.\s*(.*)', content)

    title = lines[0] if len(lines) > 0 else "제목 없음"
    summary = lines[1] if len(lines) > 1 else "요약 없음"
    description = lines[2] if len(lines) > 2 else "설명 없음"

    return title.strip(), summary.strip(), description.strip()

# === 구글 검색 링크 ===
def search_google_links(query):
    if not query or "없음" in query:
        return []

    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    try:
        res = service.cse().list(q=query, cx=GOOGLE_CX, num=3).execute()
        items = res.get("items", [])
        links = [item["link"] for item in items]
        return links
    except Exception:
        return []

# === 메인 처리 ===
def process_video_file(file_path: str):
    result = model.transcribe(file_path, verbose=False)
    segments = result["segments"]

    timeline = []
    current_start = 0
    current_end = 10
    current_text = ""

    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_text = seg["text"]

        while seg_start >= current_end:
            if current_text.strip():
                title, summary, description = summarize_section(current_text)
                references = search_google_links(summary)
            else:
                title, summary, description = "제목 없음", "요약 없음", "설명 없음"
                references = []

            timeline.append({
                "start": format_time(current_start),
                "end": format_time(current_end),
                "title": title,
                "summary": summary,
                "description": description,
                "reference_links": references
            })

            current_start = current_end
            current_end += 10
            current_text = ""

        current_text += " " + seg_text

    if current_text.strip():
        title, summary, description = summarize_section(current_text)
        references = search_google_links(summary)
        timeline.append({
            "start": format_time(current_start),
            "end": format_time(current_end),
            "title": title,
            "summary": summary,
            "description": description,
            "reference_links": references
        })

    return timeline

# === API 엔드포인트 ===
@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    with NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
        temp.write(await file.read())
        temp_path = temp.name

    try:
        summary_result = process_video_file(temp_path)
        return JSONResponse(content={"result": summary_result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        os.remove(temp_path)