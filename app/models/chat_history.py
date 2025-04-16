from sqlalchemy import Column, Integer, String, DateTime, Vector, text
from models.connection import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), nullable=False)
    conversation_id = Column(Integer, nullable=False)
    context = Column(String(1000), nullable=False)
    embed = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))