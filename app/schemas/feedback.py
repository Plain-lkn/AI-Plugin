from pydantic import BaseModel

class Feedback(BaseModel):
    user_id: str
    pdf_url: str