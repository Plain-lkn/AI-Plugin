from app.models.history import History
from app.schemas.history import HistoryBase
from sqlalchemy.ext.asyncio import AsyncSession

async def create_history(history_base: HistoryBase, session: AsyncSession):
    try:
        history_dict = history_base.model_dump()
        history = History(**history_dict)

        session.add(history)
        session.commit()
        session.refresh(history)
        return history
    except Exception as e:
        session.rollback()
        raise e
