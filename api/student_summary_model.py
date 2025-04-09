from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class StudentSummary(Base):
    __tablename__ = "student_summaries"

    student_id = Column(String, primary_key=True)
    name = Column(String)
    summary = Column(String)  # 요약 텍스트

# DB 연결 및 테이블 생성
engine = create_engine("postgresql://user:password@localhost/mydb")
Base.metadata.create_all(engine)

# 세션 생성
Session = sessionmaker(bind=engine)
session = Session()

# 예시 데이터 삽입
summary = StudentSummary(
    student_id="A123",
    name="김지원",
    summary="문법은 부족하지만 구조와 창의성이 뛰어나지만 논리 흐름은 개선이 필요합니다."
)

session.add(summary)
session.commit()

# 요약 불러오기 함수
def get_student_summary(student_id):
    summary = session.query(StudentSummary).filter_by(student_id=student_id).first()
    return summary.summary if summary else "요약 정보 없음"