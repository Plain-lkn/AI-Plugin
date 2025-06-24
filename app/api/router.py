from fastapi import APIRouter
from app.api.ai.chat import router as chat_router
from app.api.ai.video_summary import router as video_summary_router
from app.api.ai.feedback import router as feedback_router
from app.api.ai.summary_by_timestep import router as sbt_router
from app.api.ai.speech import router as speech_router

router = APIRouter()

router.include_router(chat_router)
router.include_router(video_summary_router)
router.include_router(feedback_router)
router.include_router(sbt_router)
router.include_router(speech_router)