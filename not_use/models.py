from sqlalchemy import Column, Integer, String, Vector
from app.models.db import Base

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True)
    student_id = Column(String(30))
    class_name = Column(String(50))
    content = Column(String(500))
    embedding = Column(Vector(1536))  # GPT-4O 임베딩 벡터 길이