from sqlalchemy import Column, Integer, String, DateTime, Text
from pgvector.sqlalchemy import Vector
from app.db.connection import Base

class History(Base):
    __tablename__ = "history"

    id = Column(String(40), primary_key=True)
    user_id = Column(String(30), nullable=False)
    conversation_id = Column(Integer, nullable=False)
    context = Column(Text, nullable=False)
    embed = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime, nullable=False)