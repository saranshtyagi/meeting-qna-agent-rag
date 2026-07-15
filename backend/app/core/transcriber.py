# import os
# import traceback
# from groq import Groq
# from app.config import settings

# if not settings.GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY is not set in your .env file")

# client = Groq(
#     api_key=settings.GROQ_API_KEY
# )

# def transcribe_chunk(chunk_path: str) -> str:
#     """
#     Transcribe a single audio chunk using Groq Whisper.
#     """

#     print("\n" + "=" * 60)
#     print("TRANSCRIBING CHUNK")
#     print("=" * 60)
#     print(f"File      : {chunk_path}")
#     print(f"Exists    : {os.path.exists(chunk_path)}")
#     print(f"Model     : {settings.GROQ_WHISPER_MODEL}")
#     print(f"API Key   : {settings.GROQ_API_KEY[:10]}...")
#     print(f"File Size : {os.path.getsize(chunk_path)/1024/1024:.2f} MB")

#     try:
#         with open(chunk_path, "rb") as audio_file:

#             print("Sending request to Groq...")

#             transcription = client.audio.transcriptions.create(
#                 file=audio_file,
#                 model=settings.GROQ_WHISPER_MODEL
#             )

#             print("Response received successfully!")

#         print("Transcript length:", len(transcription.text))

#         return transcription.text.strip()

#     except Exception as e:
#         print("\n❌ Groq transcription failed!")
#         print("Exception Type:", type(e).__name__)
#         print("Exception:", e)

#         print("\nFull traceback:")
#         traceback.print_exc()

#         raise


# def transcribe_all(chunks: list) -> str:
#     """
#     Transcribe all chunks and combine them.
#     """

#     print(f"\nUsing Groq Whisper ({settings.GROQ_WHISPER_MODEL})")
#     print(f"Total chunks: {len(chunks)}")

#     transcripts = []

#     for i, chunk in enumerate(chunks, start=1):
#         print(f"\n---------- Chunk {i}/{len(chunks)} ----------")
#         transcripts.append(transcribe_chunk(chunk))

#     print("\n Transcription complete.")

#     return " ".join(transcripts).strip()

import os
import shutil
import subprocess
import tempfile
import traceback
from pathlib import Path

from groq import Groq

from app.config import settings

if not settings.GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set.")

client = Groq(
    api_key=settings.GROQ_API_KEY,
)


# -------------------------------------------------------
# Whisper
# -------------------------------------------------------

def transcribe_chunk(chunk_path: str) -> str:

    print(f"\nTranscribing {Path(chunk_path).name}")

    try:

        with open(chunk_path, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(

                file=audio_file,

                model=settings.GROQ_WHISPER_MODEL,

            )

        return transcription.text.strip()

    except Exception:

        traceback.print_exc()

        raise


# -------------------------------------------------------
# Generator
# -------------------------------------------------------

def iter_chunks(
    wav_path: str,
    chunk_minutes: int = 2,
):

    temp_dir = tempfile.mkdtemp()

    try:

        pattern = os.path.join(
            temp_dir,
            "chunk_%03d.wav",
        )

        subprocess.run(

            [

                "ffmpeg",

                "-y",

                "-i",

                wav_path,

                "-f",

                "segment",

                "-segment_time",

                str(chunk_minutes * 60),

                "-c",

                "copy",

                pattern,

            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL,

            check=True,

        )

        chunks = sorted(
            Path(temp_dir).glob("chunk_*.wav")
        )
        print("Preparing transcription...")
        print(f"\nTotal chunks: {len(chunks)}")

        for chunk in chunks:

            yield str(chunk)

    finally:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )


# -------------------------------------------------------
# Public
# -------------------------------------------------------

def transcribe_audio(
    wav_path: str,
) -> str:

    transcript = []

    for chunk in iter_chunks(wav_path):

        transcript.append(
            transcribe_chunk(chunk)
        )

        try:
            os.remove(chunk)
        except OSError:
            pass

    print("\nTranscription Complete.")

    return " ".join(transcript)