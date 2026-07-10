from pathlib import Path
import shutil
import tempfile

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.schemas.meeting import MeetingResponse
from app.services.meeting_service import MeetingService
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from typing import List
from app.schemas.meeting_list import MeetingListResponse
from app.schemas.meeting_detail import MeetingDetailResponse



router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
)

def get_meeting_service(
    db: Session = Depends(get_db),
):

    return MeetingService(db)

@router.post(
    "",
    response_model=MeetingResponse,
)
async def analyze_meeting(

    youtube_url: str | None = Form(default=None),

    file: UploadFile | None = File(default=None),

    service: MeetingService = Depends(get_meeting_service),

):

    if youtube_url is None and file is None:

        raise HTTPException(
            status_code=400,
            detail="Provide either a YouTube URL or an audio file.",
        )

    if youtube_url and file:

        raise HTTPException(
            status_code=400,
            detail="Provide only one input.",
        )

    if youtube_url:

        return service.process(youtube_url)

    suffix = Path(file.filename).suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp:

        shutil.copyfileobj(
            file.file,
            temp,
        )

        temp_path = temp.name

    return service.process(temp_path)

@router.get(
    "",
    response_model=List[MeetingListResponse],
)
def get_all_meetings(

    service: MeetingService = Depends(get_meeting_service),

):

    return service.get_all_meetings()

@router.get(
    "/{meeting_id}",
    response_model=MeetingDetailResponse,
)
def get_meeting(

    meeting_id: str,

    service: MeetingService = Depends(get_meeting_service),

):

    return service.get_meeting(meeting_id)

@router.delete(
    "/{meeting_id}",
)
def delete_meeting(

    meeting_id: str,

    service: MeetingService = Depends(get_meeting_service),

):

    return service.delete_meeting(meeting_id)