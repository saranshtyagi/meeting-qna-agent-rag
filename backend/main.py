from fastapi import FastAPI

from app.api.router import api_router
from app.db.database import Base
from app.db.database import engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(

    title="AI Meeting Assistant API",

    version="1.0.0",

    description="Backend API for AI Meeting Assistant",

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://meeting-agent-frontend-swart.vercel.app/"
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://192.168.1.7:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)