from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from gtts import gTTS
from pydub import AudioSegment
from openai import OpenAI
import uuid
import os
import nltk

# NLTK 초기화
nltk.download("punkt")

# FastAPI 인스턴스
router = APIRouter()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 오디오 파일 저장 폴더
AUDIO_FOLDER = "audios/"
os.makedirs(AUDIO_FOLDER, exist_ok=True)


# 사용자 입력 모델
class TextInput(BaseModel):
    text: str


# 문단에서 의문문 추출 함수
def extract_questions_korean(text):
    prompt = f"""
    다음 문단에서 질문(의문문)으로 추정되는 문장만 골라서 리스트로 출력해 줘. 
    질문이 명확하지 않아도 질문처럼 보이는 문장이 있다면 포함해 줘.

    문단:
    \"\"\"{text}\"\"\"

    결과는 아래와 같은 형식으로 출력해 줘:
    ["문장1", "문장2", ...]
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    output = response.choices[0].message.content.strip()

    try:
        return eval(output) # GPT가 리스트로 줄 것을 기대
    except Exception as e:
        print(f"Error parsing GPT output: {output}")
        return []


# ChatGPT 답변 생성 함수
def ask_chatgpt(question):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content.strip()


# 텍스트를 음성으로 변환 (gTTS)
def text_to_speech(text, filename, speed_factor=1.2):
    # gTTS로 음성 생성
    tts = gTTS(text, lang="ko")
    filepath = os.path.join(AUDIO_FOLDER, filename)
    tts.save(filepath)

    # pydub을 사용해 음성 파일 로드
    audio = AudioSegment.from_mp3(filepath)

    # 속도를 1.5배로 변경
    altered_audio = audio.speedup(playback_speed=speed_factor)

    # 변경된 파일 저장
    altered_audio.export(filepath, format="mp3")

# POST /ask : 문단에서 질문 추출 후 각각 응답 처리
@router.post("/ask")
def process_text(request: TextInput):
    print(request)
    questions = extract_questions_korean(request.text)
    results = []

    for question in questions:
        answer = ask_chatgpt(question)
        audio_filename = f"{uuid.uuid4().hex}.mp3"
        text_to_speech(answer, audio_filename)
        results.append({
            "question": question,
            "answer": answer,
            "audio_filename": audio_filename
        })

    return JSONResponse(content={"results": results})


# GET /audio/{filename} : 생성된 음성 파일 반환
@router.get("/audio/{filename}")
def get_audio(filename: str):
    path = os.path.join(AUDIO_FOLDER, filename)
    print(path)
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    return JSONResponse(content={"error": "파일이 존재하지 않음"}, status_code=404)