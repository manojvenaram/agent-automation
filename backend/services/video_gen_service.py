"""
AI Video Generation Service.
Integrates with Free/Open Generative AI video endpoints (e.g. HuggingFace Serverless, Luma, or Kling).
Includes robust retry handling for free-tier rate limits.
"""

import os
import time
import requests
from pathlib import Path
from backend.core.config import settings
from backend.core.logging import logger

class VideoGenService:
    def __init__(self):
        # We use HuggingFace API key from settings or a default free provider key
        self.api_key = settings.hf_api_key or os.getenv("FREE_VIDEO_API_KEY", "")
        # Using a true text-to-video model endpoint
        self.api_url = "https://api-inference.huggingface.co/models/ali-vilab/text-to-video-ms-1.7b"

    def _call_api_with_retry(self, payload: dict, max_retries: int = 3) -> bytes:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
                
                # Check for rate limits or model loading (common on free tier)
                if response.status_code == 503:
                    logger.warning(f"Video model is loading, waiting 30s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(30)
                    continue
                elif response.status_code == 429:
                    logger.warning(f"Video rate limited, waiting 45s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(45)
                    continue
                    
                response.raise_for_status()
                return response.content
            except requests.exceptions.ConnectionError as ce:
                # Fail fast on ISP blocks or DNS failures to prevent spamming the console with retries
                logger.debug(f"Network block detected: {ce}")
                raise RuntimeError("Video API is unreachable due to network blocking. Triggering fallback.")
            except Exception as e:
                logger.debug(f"Video API call failed (Attempt {attempt+1}): {e}")
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to generate video after {max_retries} attempts.")
                time.sleep(5)
        
        raise RuntimeError("Failed to generate video.")

    def generate_video(self, prompt: str, output_path: str) -> str:
        """Generates a video clip from a text prompt and saves it to output_path."""
        logger.info(f"Generating video for prompt: {prompt[:50]}...")
        
        if not self.api_key:
            logger.warning("No Video API key provided! Returning a placeholder dummy video path.")
            # For 100% free offline mode without keys, we might fallback to a blank/stock video
            # Here we just raise an error or copy a sample
            if Path("sample.mp4").exists():
                import shutil
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy("sample.mp4", output_path)
                return output_path
            raise ValueError("HF_API_KEY or FREE_VIDEO_API_KEY must be set in .env")

        payload = {
            "inputs": prompt,
            "parameters": {
                "num_frames": 24, # e.g. 1 second at 24fps
                "width": settings.video_width,
                "height": settings.video_height
            }
        }
        
        video_bytes = self._call_api_with_retry(payload)
        
        out_dir = Path(output_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(video_bytes)
            
        logger.info(f"Successfully generated video: {output_path}")
        return output_path

# Global singleton
video_gen_service = VideoGenService()
