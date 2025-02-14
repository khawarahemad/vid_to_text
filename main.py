from fastapi import FastAPI, HTTPException
from yt_dlp import YoutubeDL
import whisper
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
model = whisper.load_model("base")  # Load Whisper model once
executor = ThreadPoolExecutor()

# Ensure temp folder exists
os.makedirs("temp", exist_ok=True)

def download_subtitles(url: str, video_id: str, lang: str = 'en') -> str:
    """Downloads subtitles from YouTube if available."""
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'subtitleslangs': [lang],
        'subtitlesformat': 'vtt',
        'outtmpl': f'temp/{video_id}',
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    subtitle_path = f'temp/{video_id}.{lang}.vtt'
    if os.path.exists(subtitle_path):
        with open(subtitle_path, 'r') as f:
            transcript = f.read()
        os.remove(subtitle_path)  # Cleanup
        return transcript
    return ""

async def transcribe_audio(url: str, video_id: str) -> str:
    """Downloads audio and transcribes it using Whisper."""
    loop = asyncio.get_event_loop()
    audio_path = f"temp/{video_id}.wav"
    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"temp/{video_id}",  # No .wav extension here
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': '192'}],
        'quiet': False,  # Enable verbose logging
    }
    try:
        print(f"Downloading audio for transcription: {url}")
        with YoutubeDL(audio_opts) as ydl:
            await loop.run_in_executor(executor, lambda: ydl.download([url]))

        # Ensure the correct filename
        if not os.path.exists(audio_path):
            raise HTTPException(500, detail="Failed to download audio for transcription.")

        print(f"Transcribing audio: {audio_path}")
        result = await loop.run_in_executor(executor, lambda: model.transcribe(audio_path))
        transcript = result.get("text", "").strip()
        print("Whisper Output:", transcript)  # Debugging output
        return transcript
    except Exception as e:
        print(f"Error during audio download or transcription: {str(e)}")
        raise HTTPException(500, detail=f"Failed to process audio: {str(e)}")
    finally:
        # Ensure file cleanup after processing
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Deleted file: {audio_path}")


@app.get("/get_video_details")
async def get_video_details(url: str, lang: str = 'en'):
    """Fetches video details and gets transcript (subtitles or Whisper)."""
    if 'youtube.com/watch?v=' not in url and 'youtu.be/' not in url:
        raise HTTPException(400, detail="Invalid YouTube URL")

    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(
                executor, lambda: ydl.extract_info(url, download=False)
            )
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to fetch video info: {str(e)}")

    video_id = info.get('id', 'unknown')
    transcript = ""

    # Always attempt subtitles first
    transcript = await asyncio.get_event_loop().run_in_executor(
        executor, lambda: download_subtitles(url, video_id, lang))

    # If subtitles fail, transcribe audio
    if not transcript.strip():
        transcript = await transcribe_audio(url, video_id)

    return {
        'title': info.get('title'),
        'description': info.get('description'),
        'duration': info.get('duration'),
        'views': info.get('view_count'),
        'upload_date': info.get('upload_date'),
        'channel': info.get('channel'),
        'transcript': transcript,
    }
