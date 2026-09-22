"""
Central Configuration for YouTube Shorts Automation Agent.
All paths, media dimensions, AI model names, and system thresholds are defined here.
Zero paid APIs required.
"""

from pathlib import Path
from typing import List, Optional, Dict
import os
from pydantic import BaseModel, Field

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application directories
PROJECTS_DIR = BASE_DIR / "projects"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"
CREDENTIALS_DIR = BASE_DIR / "credentials"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
TURBOVEC_DIR = MEMORY_DIR / "turbovec"

# Ensure essential directories exist
for directory in [PROJECTS_DIR, ASSETS_DIR, MUSIC_DIR, FONTS_DIR, CREDENTIALS_DIR, LOGS_DIR, TURBOVEC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class AppConfig(BaseModel):
    # Environment & Operating Modes
    environment: str = Field(default="development")
    demo_mode: bool = Field(default=False)
    auto_publish: bool = Field(default=True)
    content_mode: str = Field(default="AUTONOMOUS")  # "AUTONOMOUS" or "MANUAL"
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # AI / LLM (Ollama / Gemini / Groq / HuggingFace)
    llm_provider: str = Field(default="groq")
    gemini_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")
    hf_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.1-8b-instant")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="qwen2.5:3b")
    llm_timeout: int = Field(default=60)
    llm_temperature: float = Field(default=0.7)

    # Text-To-Speech (TTS)
    tts_engine: str = Field(default="edge-tts")  # 'edge-tts' or 'pyttsx3'
    tts_voice: str = Field(default="en-US-ChristopherNeural")
    tts_rate: str = Field(default="+0%")
    tts_pitch: str = Field(default="+0Hz")

    # Video Specifications (YouTube Shorts Target)
    video_width: int = Field(default=1080)
    video_height: int = Field(default=1920)
    video_fps: int = Field(default=30)
    min_duration: int = Field(default=20)
    max_duration: int = Field(default=60)
    target_words_per_minute: int = Field(default=145)

    # Captions & Subtitles
    caption_font_size: int = Field(default=64)
    caption_position: str = Field(default="bottom_safe")
    caption_max_words_per_line: int = Field(default=4)

    # Quality Control & Fact Checking
    fact_confidence_threshold: float = Field(default=0.80)
    minimum_quality_score: int = Field(default=75)
    max_repair_attempts: int = Field(default=3)

    # Universal Content Categories (Non-restricted)
    topic_categories: List[str] = Field(
        default_factory=lambda: [
            "news",
            "sports",
            "entertainment",
            "humor",
            "cartoons",
            "science",
            "history",
            "technology",
            "gaming",
            "education",
            "animals",
            "geography",
            "mystery",
            "food",
            "space",
            "internet culture",
            "original fiction",
        ]
    )

    # Content Portfolio Target Mix (Default Weights, adjusted dynamically by Content Brain)
    portfolio_mix: Dict[str, float] = Field(
        default_factory=lambda: {
            "reddit_stories": 0.25,
            "quizzes": 0.20,
            "shower_thoughts": 0.20,
            "motivational": 0.15,
            "did_you_know": 0.10,
            "science": 0.05,
            "trending": 0.05,
        }
    )

    # Audience Geographic Priorities (Initial Targets)
    target_audiences: List[str] = Field(
        default_factory=lambda: [
            "United States",
            "Canada",
            "United Kingdom",
            "Australia",
            "New Zealand",
        ]
    )

    # YouTube Integration
    youtube_client_secrets_file: Path = Field(default=CREDENTIALS_DIR / "client_secrets.json")
    youtube_token_file: Path = Field(default=CREDENTIALS_DIR / "token.pickle")
    youtube_privacy_status: str = Field(default="private")
    youtube_category_id: str = Field(default="28")  # 28 = Science & Technology
    youtube_comments_enabled: bool = Field(default=False)

    # Telegram Bot Integration
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")
    
    # Scheduler Settings
    scheduler_enabled: bool = Field(default=False)
    posting_time: str = Field(default="18:00")
    timezone: str = Field(default="UTC")
    shorts_per_day: int = Field(default=2)
    
    # TurboVec & Semantic Memory Configuration
    memory_backend: str = Field(default="turbovec")  # 'turbovec' or 'sqlite'
    turbovec_enabled: bool = Field(default=True)
    turbovec_index_path: Path = Field(default=TURBOVEC_DIR / "index.tvec")
    turbovec_bits: int = Field(default=4)
    turbovec_autosave: bool = Field(default=True)
    turbovec_sync_interval: int = Field(default=10)
    turbovec_max_results: int = Field(default=10)
    turbovec_batch_size: int = Field(default=8)

    # Local Embeddings Configuration
    embedding_provider: str = Field(default="local")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)
    embedding_batch_size: int = Field(default=8)

    # Hardware & Cache Optimizations
    cache_max_gb: float = Field(default=10.0)
    render_mode: str = Field(default="low_resource") # 'standard' or 'low_resource'
    max_concurrent_ai_tasks: int = Field(default=1)
    hardware_profile_path: Path = Field(default=DATA_DIR / "hardware_profile.json")


def load_config() -> AppConfig:
    """Load configuration with environment variable overrides."""
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    
    config_dict = {}
    
    # Check environment variables
    env_mappings = {
        "ENVIRONMENT": "environment",
        "DEMO_MODE": lambda v: ("demo_mode", v.lower() == "true"),
        "AUTO_PUBLISH": lambda v: ("auto_publish", v.lower() == "true"),
        "HOST": "host",
        "PORT": lambda v: ("port", int(v)),
        "DEBUG": lambda v: ("debug", v.lower() == "true"),
        "LLM_PROVIDER": "llm_provider",
        "GEMINI_API_KEY": "gemini_api_key",
        "GROQ_API_KEY": "groq_api_key",
        "HF_API_KEY": "hf_api_key",
        "GROQ_MODEL": "groq_model",
        "OLLAMA_BASE_URL": "ollama_base_url",
        "OLLAMA_MODEL": "ollama_model",
        "LLM_TIMEOUT": lambda v: ("llm_timeout", int(v)),
        "TTS_ENGINE": "tts_engine",
        "TTS_VOICE": "tts_voice",
        "TTS_RATE": "tts_rate",
        "TTS_PITCH": "tts_pitch",
        "VIDEO_WIDTH": lambda v: ("video_width", int(v)),
        "VIDEO_HEIGHT": lambda v: ("video_height", int(v)),
        "VIDEO_FPS": lambda v: ("video_fps", int(v)),
        "MIN_DURATION": lambda v: ("min_duration", int(v)),
        "MAX_DURATION": lambda v: ("max_duration", int(v)),
        "TARGET_WORDS_PER_MINUTE": lambda v: ("target_words_per_minute", int(v)),
        "FACT_CONFIDENCE_THRESHOLD": lambda v: ("fact_confidence_threshold", float(v)),
        "MINIMUM_QUALITY_SCORE": lambda v: ("minimum_quality_score", int(v)),
        "MAX_REPAIR_ATTEMPTS": lambda v: ("max_repair_attempts", int(v)),
        "YOUTUBE_PRIVACY_STATUS": "youtube_privacy_status",
        "YOUTUBE_CATEGORY_ID": "youtube_category_id",
        "SCHEDULER_ENABLED": lambda v: ("scheduler_enabled", v.lower() == "true"),
        "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
        "TELEGRAM_CHAT_ID": "telegram_chat_id",
        "POSTING_TIME": "posting_time",
        "TIMEZONE": "timezone",
        "MEMORY_BACKEND": "memory_backend",
        "TURBOVEC_ENABLED": lambda v: ("turbovec_enabled", v.lower() == "true"),
        "TURBOVEC_BITS": lambda v: ("turbovec_bits", int(v)),
        "TURBOVEC_AUTOSAVE": lambda v: ("turbovec_autosave", v.lower() == "true"),
        "TURBOVEC_SYNC_INTERVAL": lambda v: ("turbovec_sync_interval", int(v)),
        "TURBOVEC_MAX_RESULTS": lambda v: ("turbovec_max_results", int(v)),
        "TURBOVEC_BATCH_SIZE": lambda v: ("turbovec_batch_size", int(v)),
        "EMBEDDING_PROVIDER": "embedding_provider",
        "EMBEDDING_MODEL": "embedding_model",
        "EMBEDDING_DIMENSION": lambda v: ("embedding_dimension", int(v)),
        "EMBEDDING_BATCH_SIZE": lambda v: ("embedding_batch_size", int(v)),
        "CACHE_MAX_GB": lambda v: ("cache_max_gb", float(v)),
        "RENDER_MODE": "render_mode",
        "MAX_CONCURRENT_AI_TASKS": lambda v: ("max_concurrent_ai_tasks", int(v)),
    }

    for env_key, handler in env_mappings.items():
        val = os.getenv(env_key)
        if val is not None:
            if callable(handler):
                k, v = handler(val)
                config_dict[k] = v
            else:
                config_dict[handler] = val

    return AppConfig(**config_dict)


# Global singleton instance
settings = load_config()
