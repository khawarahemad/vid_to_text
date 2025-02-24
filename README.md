# VidToText - AI-Powered Video and File to Text Converter

Welcome to **VidToText**, a powerful backend tool that allows you to:
- **Chat with AI** using Hugging Face's inference API.
- **Convert YouTube videos to text** using Whisper for speech-to-text transcription.
- **Extract text from files** (PDFs, images, etc.) using OCR and PDF processing.
- **Summarize content** for quick insights.

This tool is built with **FastAPI** and integrates multiple technologies to provide a seamless experience for converting multimedia content into text and interacting with AI.

---

## Features
1. **YouTube Video to Text**:
   - Provide a YouTube video link, and the tool will download the audio, transcribe it, and return the text.
2. **File to Text**:
   - Upload PDFs or images, and the tool will extract text using OCR (Optical Character Recognition).
3. **AI Chat**:
   - Interact with Hugging Face's inference API for chatting, summarization, and more.
4. **Summarization**:
   - Summarize long texts or transcripts for quick insights.

---

## Installation Guide

### Prerequisites
1. **Python 3.8 or higher**.
2. **FFmpeg** (for audio processing).
3. **Tesseract OCR** (for text extraction from images).
4. **Poppler** (for PDF to image conversion).

#### Install System Dependencies
- **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install ffmpeg tesseract-ocr poppler-utils
  ```
- **macOS** (using Homebrew):
  ```bash
  brew install ffmpeg tesseract poppler
  ```
- **Windows**:
  - Download and install [FFmpeg](https://ffmpeg.org/download.html), [Tesseract OCR](https://github.com/tesseract-ocr/tesseract), and [Poppler](http://blog.alivate.com.au/poppler-windows/).
  - Add them to your system PATH.

---

### Step 1: Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/khawarahemad/vid_to_text.git
cd vid_to_text
```

---

### Step 2: Set Up a Virtual Environment (Optional but Recommended)
Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

### Step 3: Install Python Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```
### or 
install it with pip 
```bash
pip install fastapi uvicorn yt-dlp openai python-dotenv PyPDF2 pdf2image pillow pytesseract requests
```

---

### Step 4: Set Up Environment Variables
1. Create a `.env` file in the root directory:
   ```bash
   touch .env
   ```
2. Add your Hugging Face API key to the `.env` file:
   ```plaintext
   HUGGING_FACE_API_KEY=past_your_api_here
   ```
   Replace `paste_your_api_here` with your actual Hugging Face API key.

#### How to Get Your Hugging Face API Key
1. Go to [Hugging Face](https://huggingface.co).
2. Log in to your account.
3. Navigate to your profile > Settings > Access Tokens.
4. Click on **New Token**.
5. Enable the following permissions:
   - **Read access to contents of all repos under your personal namespace**.
   - **Read access to contents of all public gated repos you can access**.
   - **Make calls to inference providers**.
6. Scroll down, save the token, and copy it.
7. Paste the token in the `.env` file, replacing `paste_your_api_here`.

---

### Step 5: Run the Application
Start the FastAPI server:
```bash
uvicorn main:app --reload
```
- The application will be available at `http://127.0.0.1:8000`.

---

## API Endpoints

### 1. **Chat with AI**
- **Endpoint**: `/chat`
- **Method**: `POST`
- **Input**: `{"message": "Your message here"}`
- **Output**: AI-generated response.

### 2. **YouTube Video to Text**
- **Endpoint**: `/youtube-to-text`
- **Method**: `POST`
- **Input**: `{"url": "YouTube video URL"}`
- **Output**: Transcribed text from the video.

### 3. **File to Text**
- **Endpoint**: `/file-to-text`
- **Method**: `POST`
- **Input**: Upload a file (PDF or image).
- **Output**: Extracted text from the file.

### 4. **Summarize Text**
- **Endpoint**: `/summarize`
- **Method**: `POST`
- **Input**: `{"text": "Long text to summarize"}`
- **Output**: Summarized text.

---

## Example Usage

### Chat with AI
```bash
curl -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d '{"message": "Hello, how are you?"}'
```

### YouTube Video to Text
```bash
curl -X POST "http://127.0.0.1:8000/youtube-to-text" -H "Content-Type: application/json" -d '{"url": "https://www.youtube.com/watch?v=example"}'
```

### File to Text
```bash
curl -X POST "http://127.0.0.1:8000/file-to-text" -H "Content-Type: multipart/form-data" -F "file=@example.pdf"
```

### Summarize Text
```bash
curl -X POST "http://127.0.0.1:8000/summarize" -H "Content-Type: application/json" -d '{"text": "Long text to summarize..."}'
```

---

## Contributing
Contributions are welcome! If you'd like to contribute, please:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support
If you encounter any issues or have questions, feel free to open an issue on the [GitHub repository](https://github.com/khawarahemad/vid_to_text/issues).

---

Enjoy using **VidToText**! 🚀
