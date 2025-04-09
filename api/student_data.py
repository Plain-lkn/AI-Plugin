from sqlalchemy import text
from db import SessionLocal

# 예시로 작성. 실제론 파일에서 읽거나 다른 로직을 사용할 수 있음.
def get_student_submission(student_id: str) -> str:
    # 실제 구현에서는 DB에서 제출물 불러오거나 파일 읽기
    return "이것은 학생의 에세이입니다."

def get_student_summary(student_id: str) -> str:
    session = SessionLocal()
    query = text("SELECT summary FROM student_summaries WHERE student_id = :student_id")
    result = session.execute(query, {"student_id": student_id}).scalar_one_or_none()
    session.close()
    return result if result else "요약 정보 없음"