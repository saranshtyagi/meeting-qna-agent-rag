import uuid
from concurrent.futures import ThreadPoolExecutor
import os
from sqlalchemy.orm import Session

from app.schemas.meeting import MeetingResponse
from app.schemas.analysis import MeetingAnalysis

from app.db.models import Meeting
from app.repositories.meeting_repository import MeetingRepository

from app.utils.audio_processor import process_input

from app.core.transcriber import transcribe_audio
from app.core.summarize import summarize, generate_title
from app.core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from app.core.vector_store import build_vector_store
from fastapi import HTTPException

from app.schemas.meeting_list import MeetingListResponse
from app.schemas.meeting_detail import MeetingDetailResponse
from app.schemas.audio import AudioProcessingResult
from app.services.storage_service import StorageService


class MeetingService:

    def __init__(self, db: Session):
        self.repository = MeetingRepository(db)

        self.storage = StorageService()

    # ==========================================================
    # Public API
    # ==========================================================

    def process(self, source: str) -> MeetingResponse:

        meeting_id = str(uuid.uuid4())

        print(f"\nProcessing Meeting {meeting_id}")

        # Step 1 - Prepare Audio
        audio = self._prepare_audio(source)

        # Step 2 - Transcribe
        transcript = self._transcribe(
            audio.audio_path,
        )

        try:
            os.remove(audio.audio_path)
        except OSError:
            pass

        # Step 3 - Run AI Analysis + Build Vector Store in Parallel
        with ThreadPoolExecutor(max_workers=2) as executor:

            analysis_future = executor.submit(
                self._analyze,
                transcript,
            )

            vector_future = executor.submit(
                self._build_vector_store,
                meeting_id,
                transcript,
            )

            analysis = analysis_future.result()

            # Raise exception if vector store creation fails
            vector_future.result()

        # Step 4 - Save to SQLite
        self._save_meeting(
            meeting_id=meeting_id,
            analysis=analysis,
            audio=audio,
            source=source,
        )

        # Step 5 - Return API Response
        return self._create_response(
            meeting_id,
            analysis,
        )

    # ==========================================================
    # Pipeline
    # ==========================================================

    def _prepare_audio(self, source: str):
        return process_input(source)

    def _transcribe(
        self,
        wav_path: str,
    ):
        return transcribe_audio(
            wav_path,
        )

    def _analyze(self, transcript: str) -> MeetingAnalysis:

        results = self._run_parallel_tasks(transcript)

        return MeetingAnalysis(
            title=results["title"],
            transcript=transcript,
            summary=results["summary"],
            action_items=results["action_items"],
            key_decisions=results["key_decisions"],
            open_questions=results["open_questions"],
        )

    def _run_parallel_tasks(self, transcript: str):

        with ThreadPoolExecutor(max_workers=3) as executor:

            futures = {

                "title": executor.submit(
                    generate_title,
                    transcript,
                ),

                "summary": executor.submit(
                    summarize,
                    transcript,
                ),

                "action_items": executor.submit(
                    extract_action_items,
                    transcript,
                ),

                "key_decisions": executor.submit(
                    extract_key_decisions,
                    transcript,
                ),

                "open_questions": executor.submit(
                    extract_questions,
                    transcript,
                ),
            }

            return {
                key: future.result()
                for key, future in futures.items()
            }

    def _build_vector_store(
        self,
        meeting_id: str,
        transcript: str,
    ):
        
        build_vector_store(
            meeting_id,
            transcript,
        )
       


    # ==========================================================
    # Persistence
    # ==========================================================

    def _save_meeting(
        self,
        meeting_id: str,
        analysis: MeetingAnalysis,
        audio: AudioProcessingResult,
        source: str,
    ):

        meeting = Meeting(

            id=meeting_id,

            title=analysis.title,

            youtube_url=source if source.startswith(("http://", "https://")) else None,

            transcript=analysis.transcript,

            summary=analysis.summary,

            action_items=analysis.action_items,

            key_decisions=analysis.key_decisions,

            open_questions=analysis.open_questions,
            filename=audio.filename,

            audio_path=audio.audio_path,

            duration=audio.duration,

            status="completed",

        )

        self.repository.create(meeting)

    # ==========================================================
    # Response Builder
    # ==========================================================

    def _create_response(
        self,
        meeting_id: str,
        analysis: MeetingAnalysis,
    ) -> MeetingResponse:

        return MeetingResponse(

            meeting_id=meeting_id,

            title=analysis.title,

            transcript=analysis.transcript,

            summary=analysis.summary,

            action_items=analysis.action_items,

            key_decisions=analysis.key_decisions,

            open_questions=analysis.open_questions,

        )
    
    # ==========================================================
    # Meeting History
    # ==========================================================

    def get_all_meetings(self) -> list[MeetingListResponse]:

        meetings = self.repository.get_all()

        return [
            MeetingListResponse.model_validate(meeting)
            for meeting in meetings
        ]


    def get_meeting(
        self,
        meeting_id: str,
    ) -> MeetingDetailResponse:

        meeting = self.repository.get_by_id(meeting_id)

        if meeting is None:

            raise HTTPException(
                status_code=404,
                detail="Meeting not found.",
            )

        return MeetingDetailResponse.model_validate(meeting)


    def delete_meeting(
        self,
        meeting_id: str,
    ):

        meeting = self.repository.get_by_id(
            meeting_id,
        )

        if meeting is None:

            raise HTTPException(
                status_code=404,
                detail="Meeting not found.",
            )

        self.storage.delete_meeting_assets(
            meeting,
        )

        self.repository.delete(
            meeting,
        )

        return {
            "message": "Meeting deleted successfully."
        }