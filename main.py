from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL
import whisper
import os
import asyncio
import re
import openai
import tempfile
import shutil
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
model = whisper.load_model("medium")
executor = ThreadPoolExecutor()
os.makedirs("temp", exist_ok=True)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Hugging Face API configuration
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
if not HUGGING_FACE_API_KEY:
    raise ValueError("Hugging Face API key not found in environment variables.")

# Helper function to truncate text
def truncate_text(text: str, max_chars: int = 16000) -> str:
    """Truncate text to specified number of characters."""
    return text[:max_chars] if len(text) > max_chars else text

# ChatProcessor class for handling AI responses
# ChatProcessor class for handling AI responses
class ChatProcessor:
    async def _call_mistral(self, prompt: str, max_length: int = 200, temperature: float = 0.5) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "do_sample": True,
                },
            }
            response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result[0]["generated_text"].strip()
        except Exception as e:
            raise HTTPException(500, detail=f"Mistral API error: {str(e)}")

    async def generate_ai_response(self, question: str, context: Optional[str] = None):
        try:
            truncated_context = truncate_text(context) if context else None

            if truncated_context:
                prompt = (
                    "You are a helpful assistant. Based on the provided context, answer the user's question. "
                    "If asked for a summary, provide a concise summary. "
                    "If the context doesn't contain the answer, say so.\n\n"
                    f"Context: {truncated_context}\n\n"
                    f"Question: {question}\nAnswer:"
                )
                response = await self._call_mistral(prompt, max_length=300, temperature=0.3)
            else:
                prompt = f"User: {question}\nAssistant:"
                response = await self._call_mistral(prompt, max_length=150)

            clean_response = response.replace(prompt, "").strip()
            return {"response": clean_response.split("\n")[0]}

        except HTTPException:
            raise
        except Exception as e:
            return {"response": f"Error: {str(e)}"}

    async def generate_summary(self, context: str, max_length: int = 200) -> dict:
        try:
            truncated_context = truncate_text(context)
            prompt = (
                "Provide a concise summary of the following text. "
                f"Keep it under {max_length} words.\n\n"
                f"Text: {truncated_context}\n\nSummary:"
            )
            summary = await self._call_mistral(prompt, max_length=300, temperature=0.3)
            return {"summary": summary.split("Summary:")[-1].strip()}
        except Exception as e:
            return {"error": str(e)}

    async def generate_code_response(self, question: str) -> dict:
        try:
            prompt = (
                "You are a helpful coding assistant. Provide a clear and concise code example "
                f"for the following programming question. If the question is not related to programming, "
                f"respond with 'This question is not related to programming.'\n\n"
                f"Question: {question}\nCode:"
            )
            response = await self._call_mistral(prompt, max_length=500, temperature=0.2)

            clean_response = response.replace(prompt, "").strip()
            return {"response": clean_response}

        except HTTPException:
            raise
        except Exception as e:
            return {"response": f"Error: {str(e)}"}


# Instantiate ChatProcessor globally
chat_processor = ChatProcessor()

# File processing functions
async def extract_text_from_pdf(temp_path: str) -> str:
    loop = asyncio.get_event_loop()
    
    # First try text extraction
    text = await loop.run_in_executor(executor, extract_pdf_text, temp_path)
    
    # If text is minimal, try OCR
    if len(text.strip()) < 100:
        ocr_text = await loop.run_in_executor(executor, extract_pdf_ocr, temp_path)
        text += "\n" + ocr_text
    
    return text

def extract_pdf_text(temp_path: str) -> str:
    text = ""
    with open(temp_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def extract_pdf_ocr(temp_path: str) -> str:
    text = ""
    images = convert_from_path(temp_path, dpi=200)
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text.strip()

async def extract_text_from_image(temp_path: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, extract_image_text, temp_path)

def extract_image_text(temp_path: str) -> str:
    img = Image.open(temp_path)
    return pytesseract.image_to_string(img).strip()

# API Endpoints
@app.post("/chat")
async def chat_endpoint(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    context: Optional[str] = Form(None)
):
    file_content = None
    if file:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        try:
            if file.content_type == 'application/pdf':
                file_content = await extract_text_from_pdf(temp_path)
            else:
                file_content = await extract_text_from_image(temp_path)
        finally:
            os.unlink(temp_path)

    combined_context = context or file_content

    programming_keywords = ["code", "programming", "python", "java", "javascript", "c++", "html", "css", "sql"]
    if any(keyword in message.lower() for keyword in programming_keywords):
        return await chat_processor.generate_code_response(message)
    else:
        return await chat_processor.generate_ai_response(message, combined_context)

@app.post("/summarize")
async def summarize_text(
    text: str = Form(..., description="The text content to summarize"),
    max_length: int = Form(200, gt=50, le=500, description="Maximum summary length in words")
):
    return await chat_processor.generate_summary(text, max_length)

@app.post("/extract-text")
async def handle_file_extraction(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ['application/pdf', 'image/jpeg', 'image/png']:
        raise HTTPException(400, "Unsupported file type. Supported: PDF, JPEG, PNG")
    
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name
    
    try:
        if file.content_type == 'application/pdf':
            text = await extract_text_from_pdf(temp_path)
        else:
            text = await extract_text_from_image(temp_path)
        
        return {"text": text}
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")
    finally:
        os.unlink(temp_path)

def clean_transcript(text: str) -> str:
    """Removes promotional content and improves transcript clarity."""
    promo_phrases = [
        r"(?i)don't forget to like and subscribe.*",
        r"(?i)check out our sponsor.*",
        r"(?i)follow me on (Instagram|Twitter|Facebook|TikTok).*",
        r"(?i)visit our website.*",
        r"(?i)this video is sponsored by.*",
        r"(?i)hit the notification bell.*",
        r"(?i)click the link below.*",
        r"(?i)thanks for watching.*",
        r"(?i)see you in the next (video|episode).*",
        r"(?i)stay tuned for more.*",
    ]

    for phrase in promo_phrases:
        text = re.sub(phrase, '', text, flags=re.IGNORECASE).strip()

    # Remove timestamps
    text = re.sub(r"\d{1,2}:\d{2}", "", text).strip()

    return text

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
        'outtmpl': f"temp/{video_id}",
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }
        ],
        'quiet': False,
    }

    try:
        print(f"Downloading audio for transcription: {url}")
        with YoutubeDL(audio_opts) as ydl:
            await loop.run_in_executor(executor, lambda: ydl.download([url]))

        if not os.path.exists(audio_path):
            raise HTTPException(500, detail="Failed to download audio for transcription.")

        print(f"Transcribing audio: {audio_path}")
        result = await loop.run_in_executor(executor, lambda: model.transcribe(audio_path))
        transcript = result.get("text", "").strip()

        print("Whisper Output:", transcript)

        return transcript
    except Exception as e:
        print(f"Error during audio download or transcription: {str(e)}")
        raise HTTPException(500, detail=f"Failed to process audio: {str(e)}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)  # Cleanup after transcription


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
    
    transcript = await asyncio.get_event_loop().run_in_executor(
        executor, lambda: download_subtitles(url, video_id, lang)
    )

    if not transcript.strip():
        transcript = await transcribe_audio(url, video_id)

    transcript = clean_transcript(transcript)

    return {
        'title': info.get('title'),
        'description': info.get('description'),
        'duration': info.get('duration'),
        'views': info.get('view_count'),
        'upload_date': info.get('upload_date'),
        'channel': info.get('channel'),
        'transcript': transcript,
    }