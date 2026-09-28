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
        self.api_url = "manojvibranium21/mixamo-mocap-zerogpu"

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
            logger.warning("No HF_API_KEY provided! Falling back to static image...")
            raise ValueError("HF_API_KEY must be set in .env")

        try:
            from gradio_client import Client
            logger.info(f"Connecting to ZeroGPU Video Generator for prompt: {prompt[:50]}...")
            
            client = Client("manojvibranium21/mixamo-mocap-zerogpu", token=self.api_key)
            result = client.predict(
                prompt=prompt,
                api_name="/generate_broll"
            )
            
            if result and os.path.exists(result):
                out_dir = Path(output_path).parent
                out_dir.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy(result, output_path)
                logger.info(f"Successfully generated ZeroGPU AI video: {output_path}")
                return output_path
            else:
                raise RuntimeError("ZeroGPU Space returned None.")
                
        except Exception as e:
            logger.error(f"ZeroGPU Video generation failed: {e}")
            raise RuntimeError(f"Failed to generate video: {e}")

# Global singleton
video_gen_service = VideoGenService()
