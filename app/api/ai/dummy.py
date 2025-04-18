from fastapi import APIRouter, Depends, HTTPException
from app.schemas.history import HistoryDTO
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_session
from app.crud.history import create_history

router = APIRouter()

@router.post("/dummy")
async def create_dummy_data(request: HistoryDTO, session: AsyncSession = Depends(get_session)):
    # try:
    history_data = await request.history_to_base()
    await create_history(history_data, session)
    return {"message": "성공적으로 더미데이터가 생성되었습니다."}
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))
