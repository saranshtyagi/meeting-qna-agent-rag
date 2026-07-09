from fastapi import FastAPI

from app.api.router import api_router
from app.db.database import Base
from app.db.database import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(

    title="AI Meeting Assistant API",

    version="1.0.0",

    description="Backend API for AI Meeting Assistant",

)

app.include_router(api_router)