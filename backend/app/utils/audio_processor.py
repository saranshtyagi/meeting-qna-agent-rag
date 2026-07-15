# import yt_dlp 
# from pydub import AudioSegment
# import os 
# from app.schemas.audio import AudioProcessingResult

# DOWNLOAD_DIR = 'downloads'
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# def download_youtube_audio(url: str) -> str: 
#     output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
#     ydl_opts = {
#         "format": "bestaudio/best", 
#         "outtmpl": output_path, 
#         "postprocessors": [
#             {
#                 "key": "FFmpegExtractAudio", 
#                 "preferredcodec": "wav", 
#                 "preferredquality": "192",
#             }
#         ], 
#         "quiet": True,
#     }
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download = True)
#         filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
#     return filename


# def convert_to_wav(input_path: str) -> str:
#     """Convert any audio/video file to WAV format using pydub."""
#     output_path = os.path.splitext(input_path)[0] + "_converted.wav"
#     audio = AudioSegment.from_file(input_path)
#     audio = audio.set_channels(1).set_frame_rate(16000) #16khz
#     audio.export(output_path, format="wav")
#     return output_path

# def chunk_audio(wav_path : str , chunk_minutes : int = 2) -> list: # int = 2 signifies chunks has to be created of 2 minutes each
#     audio = AudioSegment.from_wav(wav_path)
#     chunk_ms = chunk_minutes * 60 * 1000  # 2 * 60 * 1000 = 1,20,000 milliseconds 

#     chunks = []

#     for i, start in enumerate(range(0,len(audio),chunk_ms)): # from 0 to len(audio) in ms at steps of chunk_ms
#         chunk = audio[start : start + chunk_ms]
#         chunk_path = f"{wav_path}_chunk_{i}.wav"
#         chunk.export(chunk_path , format = "wav")

#         chunks.append(chunk_path)
    
#     return chunks

# def process_input(source: str) -> AudioProcessingResult:

#     if source.startswith(("http://", "https://")):

#         print("Detected YouTube URL. Downloading audio...")

#         wav_path = download_youtube_audio(source)

#     else:

#         print("Detected local file. Converting to WAV...")

#         wav_path = convert_to_wav(source)

#     print("Chunking audio...")

#     chunks = chunk_audio(wav_path)

#     print(f"Audio ready — {len(chunks)} chunk(s) created.")

#     audio = AudioSegment.from_wav(wav_path)

#     duration_seconds = int(audio.duration_seconds)

#     minutes = duration_seconds // 60

#     seconds = duration_seconds % 60

#     return AudioProcessingResult(

#         filename=os.path.basename(wav_path),

#         audio_path=wav_path,

#         duration=f"{minutes}:{seconds:02d}",

#         chunks=chunks,
#     )

import json
import os
import subprocess
from pathlib import Path

import yt_dlp
from fastapi import HTTPException
from yt_dlp.utils import DownloadError

from app.schemas.audio import AudioProcessingResult

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ==========================================================
# Download
# ==========================================================

def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s",
    )

    ydl_opts = {

        "format": "bestaudio/best",

        "outtmpl": output_path,

        "postprocessors": [

            {

                "key": "FFmpegExtractAudio",

                "preferredcodec": "wav",

                "preferredquality": "192",

            }

        ],

        "quiet": True,

    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        try:

            info = ydl.extract_info(
                url,
                download=True,
            )

        except DownloadError:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Unable to download YouTube video. "
                    "YouTube is blocking automated downloads. "
                    "Please upload the audio/video file instead."
                ),
            )

        filename = (
            ydl.prepare_filename(info)
            .replace(".webm", ".wav")
            .replace(".m4a", ".wav")
        )

    return filename


# ==========================================================
# Convert
# ==========================================================

def convert_to_wav(input_path: str) -> str:

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    command = [

        "ffmpeg",

        "-y",

        "-i",

        input_path,

        "-ac",

        "1",

        "-ar",

        "16000",

        output_path,

    ]

    subprocess.run(

        command,

        check=True,

        stdout=subprocess.DEVNULL,

        stderr=subprocess.DEVNULL,

    )

    return output_path


# ==========================================================
# Duration
# ==========================================================

def get_duration(wav_path: str) -> str:

    result = subprocess.run(

        [

            "ffprobe",

            "-v",

            "quiet",

            "-print_format",

            "json",

            "-show_format",

            wav_path,

        ],

        capture_output=True,

        text=True,

        check=True,

    )

    info = json.loads(result.stdout)

    seconds = int(float(info["format"]["duration"]))

    minutes = seconds // 60

    seconds = seconds % 60

    return f"{minutes}:{seconds:02d}"


# ==========================================================
# Chunk
# ==========================================================

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 2,
):

    output_dir = Path(wav_path).parent

    prefix = Path(wav_path).stem

    chunk_pattern = str(
        output_dir / f"{prefix}_chunk_%03d.wav"
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

            chunk_pattern,

        ],

        check=True,

        stdout=subprocess.DEVNULL,

        stderr=subprocess.DEVNULL,

    )

    return sorted(

        str(f)

        for f in output_dir.glob(
            f"{prefix}_chunk_*.wav"
        )

    )


# ==========================================================
# Public API
# ==========================================================

def process_input(source: str) -> AudioProcessingResult:

    if source.startswith(("http://", "https://")):

        print("Detected YouTube URL. Downloading audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Detected local file. Converting to WAV...")

        wav_path = convert_to_wav(source)

        print("Audio converted successfully.")

    return AudioProcessingResult(
        filename=os.path.basename(wav_path),
        audio_path=wav_path,
        duration=get_duration(wav_path),
    )