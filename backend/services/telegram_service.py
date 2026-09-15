import httpx
from typing import Optional
from pathlib import Path
from backend.core.config import settings
from backend.core.logging import logger

class TelegramService:
    def __init__(self):
        self.bot_token = settings.telegram_bot_token.strip() if settings.telegram_bot_token else ""
        self.chat_id = settings.telegram_chat_id.strip() if settings.telegram_chat_id else ""
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def is_enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_enabled():
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = httpx.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"[TelegramService] Failed to send message: {e}")
            return False

    def send_video(self, video_path: str, caption: Optional[str] = None) -> bool:
        if not self.is_enabled():
            return False

        path = Path(video_path)
        if not path.exists():
            logger.error(f"[TelegramService] Video file not found: {video_path}")
            return False

        # Telegram has a 50MB limit for bots via multipart upload
        if path.stat().st_size > 50 * 1024 * 1024:
            logger.warning(f"[TelegramService] Video too large for direct Telegram upload (>50MB). Sending text only.")
            if caption:
                self.send_message(f"📹 Video finished but too large for Telegram!\n\n{caption}")
            return False

        try:
            url = f"{self.base_url}/sendVideo"
            data = {"chat_id": self.chat_id}
            if caption:
                data["caption"] = caption
                data["parse_mode"] = "HTML"
            
            with open(path, "rb") as video_file:
                files = {"video": (path.name, video_file, "video/mp4")}
                response = httpx.post(url, data=data, files=files, timeout=60.0)
                response.raise_for_status()
            
            logger.info(f"[TelegramService] Successfully uploaded video to Telegram.")
            return True
        except Exception as e:
            logger.error(f"[TelegramService] Failed to upload video: {e}")
            return False

telegram_service = TelegramService()
