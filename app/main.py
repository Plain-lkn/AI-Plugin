from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as api_router
from app.db.db import engine
from app.db.connection import Base

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

Base.metadata.create_all(bind=engine)

@app.get("/")
async def health_check():
    return {"message": "Welcome to the docker world!!"}