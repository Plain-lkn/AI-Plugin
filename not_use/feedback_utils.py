from sqlalchemy import text
from db import SessionLocal
from openai_client import client, get_embedding

def get_related_feedbacks(student_id: str, input_text: str, class_name: str, top_k=3) -> str:
    session = SessionLocal()
    input_embedding = get_embedding(input_text)

    sql = text("""
        SELECT content FROM feedbacks
        WHERE student_id = :student_id AND class_name = :class_name
        ORDER BY embedding <=> :embedding
        LIMIT :limit
    """)
    results = session.execute(sql, {
        "student_id": student_id,
        "class_name": class_name,
        "embedding": input_embedding,
        "limit": top_k
    }).fetchall()

    session.close()
    return "\n\n".join([row[0] for row in results])


def generate_feedback(student_summary: str, related_feedbacks: str, student_text: str, class_name: str) -> str:
    prompt = f"""
당신은 {class_name} 수업의 조교입니다.
아래는 학생에 대한 과거 요약 정보입니다:

[학생 요약]
{student_summary}

이 학생이 예전에 받은 피드백입니다:
{related_feedbacks}

학생이 이번에 작성한 글입니다:
{student_text}

학생이 성장할 수 있도록 따뜻하고 구체적인 피드백을 남겨주세요.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content