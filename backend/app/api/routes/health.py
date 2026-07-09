from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["Health"])
async def root():

    return {
        "message": "AI Meeting Assistant Backend"
    }


@router.get("/health", tags=["Health"])
async def health():

    return {
        "status": "healthy"
    }