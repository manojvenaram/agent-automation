# Technology Stack

## Core Technologies

- **Language:** Python 3.12
- **Audio Synthesis:** Microsoft Edge Neural TTS (`edge-tts`)
- **Subtitle Generation:** OpenAI Whisper Large v3 Turbo (`whisper_service.py` via ZeroGPU Space)
- **Video Assembly & Motion:** FFmpeg (`imageio-ffmpeg`), MoviePy, Pillow (PIL), Manim
- **AI Models & LLM:** Google Gemini 2.5 Flash (via `google-genai`), Groq LLaMA 3.1, HuggingFace Flux.1 Schnell
- **Database & Storage:** SQLite3 (`shorts_agent.db`), TurboVec Vector Memory (`turbovec_memory.py`)
- **Web UI Studio:** FastAPI backend, Vanilla HTML5 / Modern CSS / Vanilla JS dashboard
- **Automation & Publishing:** YouTube Data API v3, Telegram Bot API, GitHub Actions runners
