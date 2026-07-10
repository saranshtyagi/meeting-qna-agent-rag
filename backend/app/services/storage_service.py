import shutil
from pathlib import Path
import gc
import time
from app.config import settings


class StorageService:

    # -----------------------------------------

    def delete_meeting_assets(
        self,
        meeting,
    ):

        self.delete_vector_store(meeting.id)

        self.delete_audio(meeting.audio_path)

        self.delete_chunks(meeting.audio_path)

    # -----------------------------------------

    def delete_vector_store(
        self,
        meeting_id: str,
    ):

        vector_path = (
            Path(settings.VECTOR_DB_DIR)
            / meeting_id
        )

        if vector_path.exists():

            gc.collect()
            time.sleep(0.5)

            shutil.rmtree(
                vector_path,
                ignore_errors=False,
            )

            print(f"Deleted Vector DB: {vector_path}")

    # -----------------------------------------

    def delete_audio(
        self,
        audio_path: str | None,
    ):

        if not audio_path:
            return

        path = Path(audio_path)

        if path.exists():

            path.unlink()

            print(f"Deleted Audio: {path}")

    # -----------------------------------------

    def delete_chunks(
        self,
        audio_path: str | None,
    ):

        if not audio_path:
            return

        audio = Path(audio_path)

        directory = audio.parent

        stem = audio.name

        for chunk in directory.glob(f"{stem}_chunk_*.wav"):

            chunk.unlink()

            print(f"Deleted Chunk: {chunk}")