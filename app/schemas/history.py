from pydantic import BaseModel
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
import uuid

class HistoryBase(BaseModel):
    id: str
    user_id: str
    conversation_id: int
    context: str
    embed: list[float]
    created_at: datetime

    async def history_to_dto(self):
        return HistoryDTO(
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            context=self.context,
        )

class HistoryDTO(BaseModel):
    user_id: str
    conversation_id: int
    context: str

    async def history_to_base(self):
        history_id = str(uuid.uuid4())
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        embed = embeddings.embed_query(self.context)
        return HistoryBase(
            id=history_id,
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            context=self.context,
            embed=embed,
            created_at=datetime.now(),
        )