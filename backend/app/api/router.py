from fastapi import APIRouter

from app.api.routes import chat
from app.api.routes import health
from app.api.routes import meetings

api_router = APIRouter()

api_router.include_router(
    health.router
)

api_router.include_router(
    meetings.router
)

api_router.include_router(
    chat.router
)