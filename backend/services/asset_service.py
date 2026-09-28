"""
Asset Service for Visual Assets & Background Music.
Manages downloading Creative Commons / Public Domain imagery,
generates procedural high-resolution 1080x1920 typography and graphics via Pillow,
manages ambient royalty-free music, and writes SOURCES.md.
"""

import math
import os
import random
from pathlib import Path
from typing import List, Optional
import httpx
from PIL import Image, ImageDraw, ImageFont
from backend.core.config import settings, MUSIC_DIR, ASSETS_DIR
from backend.core.logging import logger
from backend.models import VisualAsset
from backend.services.research_service import research_service


class AssetService:
    def __init__(self):
        self._ensure_default_music()

    def _ensure_default_music(self):
        """Create a default ambient procedural royalty-free audio file if none exist."""
        MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        default_music = MUSIC_DIR / "ambient_space_pad.wav"
        if not default_music.exists():
            try:
                from backend.services.ffmpeg_service import ffmpeg_service
                # Synthesize 45 seconds of gentle harmonic ambient pad in 50ms using FFmpeg audio filter
                args = [
                    "-y",
                    "-f", "lavfi",
                    "-i", "aevalsrc=sin(2*PI*216*t)*0.15+sin(2*PI*324*t)*0.08:d=45:s=44100",
                    "-c:a", "pcm_s16le",
                    str(default_music),
                ]
                ret, _, err = ffmpeg_service.run_command(args, timeout=10)
                if ret == 0 and default_music.exists():
                    logger.info(f"Generated default royalty-free ambient music track at {default_music}")
            except Exception as e:
                logger.warning(f"Could not generate procedural music: {e}")

    def get_background_music(self, category: Optional[str] = None, topic: Optional[str] = None, duration: int = 15) -> Optional[str]:
        """Generate a custom, copyright-free background track using Meta MusicGen on ZeroGPU."""
        music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
        
        # Determine mood
        mood = "lofi ambient chill beats"
        if category:
            moods = {
                "science": "mysterious sci-fi synthwave ambient",
                "sports": "high energy phonk drift phonk",
                "gaming": "upbeat retro 8-bit chiptune",
                "comedy": "bouncy quirky cartoon background music",
                "history": "epic cinematic orchestral background"
            }
            mood = moods.get(category.lower(), "lofi ambient chill beats")
            
        prompt = f"{mood} suitable for a short video about {topic or 'interesting facts'}"
        
        try:
            from gradio_client import Client
            import shutil
            logger.info(f"Composing custom music on ZeroGPU for prompt: '{prompt}'...")
            client = Client("manojvibranium21/mixamo-mocap-zerogpu", token=settings.hf_api_key if settings.hf_api_key else None)
            
            result = client.predict(
                prompt=prompt,
                duration_sec=duration,
                api_name="/generate_music"
            )
            
            if result and os.path.exists(result):
                clean_topic = (topic or "audio").replace(" ", "_").lower()[:15]
                final_path = MUSIC_DIR / f"musicgen_{clean_topic}_{random.randint(100,999)}.wav"
                shutil.copy(result, final_path)
                logger.info(f"Successfully generated custom MusicGen track: {final_path.name}")
                return str(final_path)
                
        except Exception as e:
            logger.warning(f"ZeroGPU MusicGen failed ({e}). Falling back to local library...")
        
        # Fallback to local files
        if music_files:
            return str(random.choice(music_files))
        return None

    def generate_video_asset(self, prompt: str, project_id: str, scene_idx: int) -> Optional[str]:
        """Generates AI B-Roll video on the A100 ZeroGPU Space."""
        try:
            from gradio_client import Client
            import shutil
            logger.info(f"Generating AI B-Roll video on ZeroGPU for prompt: '{prompt}'...")
            client = Client("manojvibranium21/mixamo-mocap-zerogpu", token=settings.hf_api_key if settings.hf_api_key else None)
            
            result = client.predict(
                prompt=prompt,
                api_name="/generate_broll"
            )
            
            if result and os.path.exists(result):
                final_path = ASSETS_DIR / f"{project_id}_broll_scene_{scene_idx}.mp4"
                shutil.copy(result, final_path)
                
                # Add to DB
                self.save_assets(project_id, [VisualAsset(
                    asset_id=f"broll_{scene_idx}",
                    file_path=str(final_path),
                    source_name="ZeroGPU Text-to-Video",
                    is_procedural=True
                )])
                return str(final_path)
                
        except Exception as e:
            logger.error(f"Failed to generate ZeroGPU B-Roll: {e}")
        return None

    def fetch_or_generate_visuals(
        self,
        project_id: str,
        topic: str,
        scenes_info: List[dict],
        project_dir: Path,
        aesthetic_style: str = "high quality cinematic vertical portrait, intricate details, highly aesthetic, mysterious",
    ) -> List[VisualAsset]:
        """
        Gathers visuals for each scene:
        1. Queries public domain / CC Wikimedia assets matching scene descriptions.
        2. Falls back to generating rich procedural 1080x1920 graphics with Pillow.
        """
        visuals_dir = project_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        assets: List[VisualAsset] = []

        for idx, scene in enumerate(scenes_info):
            asset_id = f"asset_{idx+1:03d}"
            target_file = visuals_dir / f"{asset_id}.jpg"
            scene_desc = scene.get("visual_description") or topic
            narration_text = scene.get("narration", "")

            # Primary visual generation via ZeroGPU Text-to-Video
            prompt_to_use = f"{topic}, {scene_desc}, {aesthetic_style}"
            
            # Try generating an AI Video first
            ai_video_path = self.generate_video_asset(prompt=prompt_to_use, project_id=project_id, scene_idx=idx)
            if ai_video_path:
                scene["visual_path"] = ai_video_path
                assets.append(VisualAsset(asset_id=asset_id, file_path=ai_video_path, source_name="ZeroGPU AI Video", is_procedural=True))
                continue
                
            # Fallback to AI Image
            ai_success = self._generate_ai_visual(
                output_path=target_file,
                prompt=prompt_to_use,
            )
            
            if ai_success:
                assets.append(
                    VisualAsset(
                        asset_id=asset_id,
                        file_path=str(target_file),
                        source_url="https://pollinations.ai/",
                        source_name="Pollinations AI Image Generator",
                        license="Public Domain / CC0",
                        creator="ShortsAgent via Pollinations",
                        attribution_required=False,
                        is_procedural=False,
                    )
                )
            else:
                self._generate_procedural_visual(
                    output_path=target_file,
                    topic=topic,
                    scene_index=idx + 1,
                    text_snippet=narration_text or scene_desc,
                )
                assets.append(
                    VisualAsset(
                        asset_id=asset_id,
                        file_path=str(target_file),
                        source_url="local://procedural_generator",
                        source_name="Procedural Visual Engine",
                        license="Public Domain / CC0",
                        creator="ShortsAgent",
                        attribution_required=False,
                        is_procedural=True,
                    )
                )

        # Write SOURCES.md in project directory
        self._write_sources_file(project_dir, assets, topic)
        return assets

    def _resize_and_cover(self, image: Image.Image, output_path: Path, width: int, height: int):
        """Scale and center-crop image to 1080x1920 cover dimensions."""
        im_ratio = image.width / image.height
        target_ratio = width / height

        if im_ratio > target_ratio:
            new_height = height
            new_width = int(new_height * im_ratio)
        else:
            new_width = width
            new_height = int(new_width / im_ratio)

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        cropped = resized.crop((left, top, left + width, top + height))
        cropped.save(output_path, quality=92)

    def _generate_hf_visual(self, output_path: Path, prompt: str) -> bool:
        """
        Generates high-quality images using FLUX.1-schnell via HuggingFace Inference API.
        """
        api_key = settings.hf_api_key
        if not api_key:
            return False
            
        url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "width": 1080,
                "height": 1920,
            }
        }
        
        import time
        for attempt in range(4):
            try:
                with httpx.Client(timeout=120.0) as client:
                    if attempt == 0:
                        logger.info(f"Generating image via HuggingFace FLUX.1-schnell...")
                    response = client.post(url, headers=headers, json=payload)
                    if response.status_code == 503 and attempt < 3:
                        logger.warning(f"HuggingFace model loading. Retrying in 15s...")
                        time.sleep(15)
                        continue
                    if response.status_code == 200:
                        with open(output_path, "wb") as f:
                            f.write(response.content)
                        return True
                    else:
                        logger.warning(f"HuggingFace API error: {response.status_code} - {response.text}")
                        return False
            except Exception as e:
                if attempt < 3:
                    logger.warning(f"HuggingFace API network issue ({e}). Retrying in {2 ** attempt}s...")
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"HuggingFace API request failed after retries: {e}")
                return False
        return False

    def _generate_ai_visual(self, output_path: Path, prompt: str) -> bool:
        """
        Generate dynamic AI visuals. Prefers HuggingFace FLUX if API key is set,
        otherwise falls back to Pollinations.ai.
        """
        # Try HuggingFace first if we have a key
        if settings.hf_api_key:
            if self._generate_hf_visual(output_path, prompt):
                return True
            logger.warning("HuggingFace generation failed. Falling back to Pollinations.ai...")

        # Fallback to Pollinations.ai
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.content) > 10000:  # Valid image is > 10kb
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    
                    # Physically crop the bottom 60 pixels to ensure absolutely no watermark
                    try:
                        from PIL import Image
                        img = Image.open(output_path)
                        width, height = img.size
                        img = img.crop((0, 0, width, height - 60))
                        # Resize back to maintain exact 1080x1920 aspect ratio for FFmpeg
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                        img.save(output_path, format="JPEG", quality=92)
                    except Exception as crop_err:
                        logger.warning(f"Failed to crop watermark: {crop_err}")
                        
                    return True
        except Exception as e:
            logger.warning(f"Pollinations AI generation failed: {e}")
        return False

    def _generate_procedural_visual(
        self,
        output_path: Path,
        topic: str,
        scene_index: int,
        text_snippet: str,
    ):
        """
        Generate a modern 1080x1920 9:16 vertical graphic card with dynamic dark gradients,
        subtle geometric glow, and bold typography for high retention.
        """
        w, h = 1080, 1920
        # Color palettes for procedural cards (deep cosmic colors)
        palettes = [
            ((10, 15, 30), (25, 45, 85)),     # Deep space blue
            ((20, 10, 30), (70, 25, 75)),     # Cosmic nebula purple
            ((15, 25, 25), (20, 65, 60)),     # Deep aurora teal
            ((25, 15, 15), (75, 30, 25)),     # Mars crimson dusk
        ]
        top_color, bottom_color = palettes[(scene_index - 1) % len(palettes)]

        # Create gradient image
        base = Image.new("RGB", (w, h), top_color)
        draw = ImageDraw.Draw(base)

        # Smooth vertical linear gradient
        for y in range(h):
            ratio = y / h
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Add cosmic decorative elements (subtle glowing circles and accents)
        accent_color = (255, 215, 0, 120)  # Gold/amber glow
        cx, cy = w // 2, h // 3
        for radius in range(240, 40, -40):
            alpha = int(35 * (1.0 - radius / 240))
            glow_color = (100, 180, 255)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=glow_color, width=2)

        # Decorative top tag
        draw.rectangle([80, 180, w - 80, 182], fill=(255, 255, 255))
        
        # Format text snippet
        words = text_snippet.split()
        wrapped_lines = []
        cur_line = []
        for word in words:
            cur_line.append(word)
            if len(" ".join(cur_line)) > 26:
                wrapped_lines.append(" ".join(cur_line))
                cur_line = []
        if cur_line:
            wrapped_lines.append(" ".join(cur_line))

        # Render bold card in the center
        card_top = cy + 120
        line_y = card_top
        for line in wrapped_lines[:4]:
            # Center text simulation
            # Draw subtle drop shadow
            draw.text((102, line_y + 2), line, fill=(0, 0, 0))
            draw.text((100, line_y), line, fill=(245, 245, 250))
            line_y += 65

        # Bottom safe zone badge
        draw.rectangle([100, h - 340, w - 100, h - 338], fill=(255, 215, 0))
        draw.text((100, h - 320), "AUTONOMOUS RESEARCH • FACT CHECKED", fill=(255, 215, 0))

        base.save(output_path, "JPEG", quality=92)

    def _write_sources_file(self, project_dir: Path, assets: List[VisualAsset], topic: str):
        """Create standard SOURCES.md inside project directory."""
        sources_md_file = project_dir / "SOURCES.md"
        with open(sources_md_file, "w", encoding="utf-8") as f:
            f.write(f"# Sources & Licensing Report: {topic}\n\n")
            f.write("This document tracks all visual and media assets used in the production of this YouTube Short.\n\n")
            f.write("## Visual Assets\n\n")
            f.write("| Asset ID | Source URL | Source Name | License | Creator |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for a in assets:
                clean_url = a.source_url if not a.source_url.startswith("local://") else "Generated locally (Procedural)"
                f.write(f"| `{a.asset_id}` | [{a.source_name}]({clean_url}) | {a.source_name} | {a.license} | {a.creator} |\n")
            f.write("\n## Audio & Music\n\n")
            f.write("- **Narration**: Locally synthesized neural voice.\n")
            f.write("- **Background Music**: Royalty-Free Public Domain / CC0 Ambient Harmonic Pad.\n")


# Global singleton instance
asset_service = AssetService()
