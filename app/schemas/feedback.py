from pydantic import BaseModel

class Feedback(BaseModel):
    user_id: str
    feedback: str