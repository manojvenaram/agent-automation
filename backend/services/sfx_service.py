"""
AI Sound Effects Service.
Generates procedural sound effects using HuggingFace AudioLDM.
"""

import os
import time
import requests
from pathlib import Path
from backend.core.config import settings
from backend.core.logging import logger

class SFXService:
    def __init__(self):
        self.api_key = settings.hf_api_key or os.getenv("FREE_VIDEO_API_KEY", "")
        self.api_url = "https://api-inference.huggingface.co/models/cvssp/audioldm-m-full"

    def generate_sfx(self, prompt: str, output_path: str) -> bool:
        """Generate a sound effect using AudioLDM."""
        if not self.api_key:
            logger.warning("No HF_API_KEY for SFX generation. Skipping SFX.")
            return False

        logger.info(f"Generating SFX for: {prompt}")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt}
        
        for attempt in range(3):
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
                if response.status_code == 503:
                    logger.warning("AudioLDM loading, waiting 15s...")
                    time.sleep(15)
                    continue
                if response.status_code == 200:
                    out_path = Path(output_path)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_path, "wb") as f:
                        f.write(response.content)
                    return True
                logger.warning(f"SFX API Error: {response.status_code}")
                return False
            except requests.exceptions.ConnectionError as ce:
                logger.debug(f"SFX Network block detected: {ce}")
                logger.warning("SFX API unreachable due to network block. Skipping SFX.")
                return False
            except Exception as e:
                logger.debug(f"SFX request failed (Attempt {attempt+1}): {e}")
                time.sleep(2)
        
        return False

# Global singleton
sfx_service = SFXService()
