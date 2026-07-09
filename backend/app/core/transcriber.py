import os
import traceback
from groq import Groq
from app.config import settings

if not settings.GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in your .env file")

client = Groq(
    api_key=settings.GROQ_API_KEY
)

def transcribe_chunk(chunk_path: str) -> str:
    """
    Transcribe a single audio chunk using Groq Whisper.
    """

    print("\n" + "=" * 60)
    print("TRANSCRIBING CHUNK")
    print("=" * 60)
    print(f"File      : {chunk_path}")
    print(f"Exists    : {os.path.exists(chunk_path)}")
    print(f"Model     : {settings.GROQ_WHISPER_MODEL}")
    print(f"API Key   : {settings.GROQ_API_KEY[:10]}...")
    print(f"File Size : {os.path.getsize(chunk_path)/1024/1024:.2f} MB")

    try:
        with open(chunk_path, "rb") as audio_file:

            print("Sending request to Groq...")

            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model=settings.GROQ_WHISPER_MODEL
            )

            print("Response received successfully!")

        print("Transcript length:", len(transcription.text))

        return transcription.text.strip()

    except Exception as e:
        print("\n❌ Groq transcription failed!")
        print("Exception Type:", type(e).__name__)
        print("Exception:", e)

        print("\nFull traceback:")
        traceback.print_exc()

        raise


def transcribe_all(chunks: list) -> str:
    """
    Transcribe all chunks and combine them.
    """

    print(f"\nUsing Groq Whisper ({settings.GROQ_WHISPER_MODEL})")
    print(f"Total chunks: {len(chunks)}")

    transcripts = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n---------- Chunk {i}/{len(chunks)} ----------")
        transcripts.append(transcribe_chunk(chunk))

    print("\n Transcription complete.")

    return " ".join(transcripts).strip()