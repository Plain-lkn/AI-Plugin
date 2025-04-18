from fastapi import APIRouter
from app.api.ai.chat import router as chat_router
from app.api.ai.video_summary import router as video_summary_router
from app.api.ai.dummy import router as dummy_router
router = APIRouter()

router.include_router(chat_router, prefix="/ai")
router.include_router(video_summary_router, prefix="/ai")
router.include_router(dummy_router, prefix="/ai")