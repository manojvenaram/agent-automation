"""
LTX Video Generation Service
Integrates Lightricks LTX generative video capabilities via Hugging Face Spaces.
Supports zero-GPU free cloud inference with gradio_client.
"""

import os
import shutil
import logging
from typing import Optional, Dict, Any
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)

class LTXVideoService:
    def __init__(self, hf_token: Optional[str] = None):
        """
        Initializes the LTX Video Service.
        :param hf_token: Optional Hugging Face token for higher rate limits.
        """
        self.hf_token = hf_token or os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
        self._distilled_client: Optional[Client] = None
        self._ltx25_client: Optional[Client] = None

    @property
    def distilled_client(self) -> Client:
        if self._distilled_client is None:
            logger.info("Connecting to Lightricks/ltx-video-distilled...")
            self._distilled_client = Client("Lightricks/ltx-video-distilled", hf_token=self.hf_token)
        return self._distilled_client

    @property
    def ltx25_client(self) -> Client:
        if self._ltx25_client is None:
            logger.info("Connecting to Lightricks/LTX-2.5...")
            self._ltx25_client = Client("Lightricks/LTX-2.5", hf_token=self.hf_token)
        return self._ltx25_client

    def generate_text_to_video(
        self,
        prompt: str,
        output_path: str = "output_ltx_video.mp4",
        negative_prompt: str = "worst quality, blurry, jittery, distorted",
        duration: int = 2,
        height: int = 512,
        width: int = 704
    ) -> Dict[str, Any]:
        """
        Generate a video from a text prompt using LTX-Video distilled.
        """
        try:
            logger.info(f"Generating video for prompt: '{prompt}'")
            result = self.distilled_client.predict(
                prompt=prompt,
                negative_prompt=negative_prompt,
                input_image_filepath=None,
                input_video_filepath=None,
                height_ui=height,
                width_ui=width,
                mode="text-to-video",
                duration_ui=duration,
                ui_frames_to_use=9,
                seed_ui=42,
                randomize_seed=True,
                ui_guidance_scale=1.0,
                improve_texture_flag=True,
                api_name="/text_to_video"
            )

            raw_path = result[0]["video"] if isinstance(result[0], dict) else result[0]
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            shutil.copy(raw_path, output_path)

            return {
                "success": True,
                "video_path": os.path.abspath(output_path),
                "seed": result[1] if len(result) > 1 else None,
                "prompt": prompt
            }
        except Exception as e:
            logger.error(f"Text-to-video generation failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_image_to_video(
        self,
        image_path: str,
        prompt: str = "Make this image come alive with cinematic motion, smooth animation",
        output_path: str = "output_i2v.mp4",
        duration: int = 2
    ) -> Dict[str, Any]:
        """
        Animate a static image into a video.
        """
        try:
            logger.info(f"Animating image {image_path} with prompt: '{prompt}'")
            result = self.distilled_client.predict(
                prompt=prompt,
                negative_prompt="worst quality, blurry, distorted",
                input_image_filepath=handle_file(image_path),
                input_video_filepath=None,
                height_ui=512,
                width_ui=704,
                mode="image-to-video",
                duration_ui=duration,
                ui_frames_to_use=9,
                seed_ui=42,
                randomize_seed=True,
                ui_guidance_scale=1.0,
                improve_texture_flag=True,
                api_name="/image_to_video"
            )

            raw_path = result[0]["video"] if isinstance(result[0], dict) else result[0]
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            shutil.copy(raw_path, output_path)

            return {
                "success": True,
                "video_path": os.path.abspath(output_path),
                "seed": result[1] if len(result) > 1 else None
            }
        except Exception as e:
            logger.error(f"Image-to-video generation failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_with_audio_ltx25(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        output_path: str = "output_ltx25.mp4",
        duration_s: float = 2.0
    ) -> Dict[str, Any]:
        """
        Generates unified, synchronized video and audio using LTX-2.5.
        """
        try:
            logger.info(f"Generating video + audio with LTX-2.5 for: '{prompt}'")
            img_input = handle_file(image_path) if image_path else None
            result = self.ltx25_client.predict(
                prompt=prompt,
                image_path=img_input,
                height=768,
                width=512,
                duration_s=duration_s,
                seed=42,
                decoder="conv",
                auto_len=False,
                randomize_seed=True,
                do_enhance=True,
                api_name="/run"
            )

            raw_path = result[0]
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            shutil.copy(raw_path, output_path)

            return {
                "success": True,
                "video_path": os.path.abspath(output_path),
                "enhanced_prompt": result[1] if len(result) > 1 else prompt,
                "seed": result[2] if len(result) > 2 else None
            }
        except Exception as e:
            logger.error(f"LTX-2.5 generation failed: {e}")
            return {"success": False, "error": str(e)}
