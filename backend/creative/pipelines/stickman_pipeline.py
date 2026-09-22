import math
import random
import os
import shutil
from typing import List, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.core.logging import logger
from backend.creative.cartoon_engine import CharacterPose
from backend.services.ffmpeg_service import ffmpeg_service
from backend.core.config import settings

class StickmanPipeline(BaseRenderPipeline):
    """
    Procedurally renders Stickman animations with a hand-drawn whiteboard aesthetic.
    Generates actual animated MP4 scenes.
    """
    def __init__(self):
        self.width = settings.video_width
        self.height = settings.video_height
        self.bg_color = (250, 250, 250) # Off-white whiteboard
        self.pen_color = (15, 15, 15)   # Almost black dry-erase marker
        self.fps = settings.video_fps

    def _get_font(self, size: int) -> ImageFont.ImageFont:
        font_paths = [
            "C:\\Windows\\Fonts\\segoeprb.ttf",  # Segoe Print (looks handwritten)
            "C:\\Windows\\Fonts\\comic.ttf",     # Comic Sans (looks handwritten)
            "C:\\Windows\\Fonts\\arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Linux fallback
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",                 # Linux fallback
        ]
        for p in font_paths:
            if Path(p).exists():
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _draw_wobbly_line(self, draw: ImageDraw.ImageDraw, pt1: Tuple[float, float], pt2: Tuple[float, float], width: int = 8, wobble_amount: int = 4):
        x1, y1 = pt1
        x2, y2 = pt2
        length = math.hypot(x2 - x1, y2 - y1)
        if length == 0:
            return
            
        segments = max(3, int(length / 30))
        pts = [(x1, y1)]
        
        for i in range(1, segments):
            t = i / segments
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            ox = random.randint(-wobble_amount, wobble_amount)
            oy = random.randint(-wobble_amount, wobble_amount)
            pts.append((int(cx + ox), int(cy + oy)))
            
        pts.append((x2, y2))
        
        draw.line(pts, fill=self.pen_color, width=width, joint="curve")
        pts2 = [(p[0] + random.randint(-1, 1), p[1] + random.randint(-1, 1)) for p in pts]
        draw.line(pts2, fill=(40, 40, 40, 150), width=max(1, width - 2), joint="curve")

    def _draw_wobbly_circle(self, draw: ImageDraw.ImageDraw, center: Tuple[float, float], radius: float, width: int = 8):
        cx, cy = center
        segments = 36
        pts = []
        for i in range(segments + 2):
            angle = (i * 2 * math.pi) / segments
            r = radius + random.randint(-3, 3)
            x = cx + int(r * math.cos(angle))
            y = cy + int(r * math.sin(angle))
            pts.append((x, y))
            
        draw.line(pts, fill=self.pen_color, width=width, joint="curve")

    def _draw_stickman(self, draw: ImageDraw.ImageDraw, cx: float, cy: float, pose: CharacterPose, frame_idx: int):
        # Bobbing animation
        bob = math.sin(frame_idx * 0.2) * 15
        cy += bob
        
        head_radius = 80
        head_center = (cx, cy - 250)
        
        self._draw_wobbly_circle(draw, head_center, head_radius)
        
        spine_top = (cx, cy - 170)
        spine_bottom = (cx, cy + 100)
        
        # Talking mouth animation
        is_talking = frame_idx % 10 < 5
        mouth_offset = 5 if is_talking else 0

        if pose == CharacterPose.SHOCKED:
            self._draw_wobbly_circle(draw, (cx - 30, cy - 260), 15, width=4)
            self._draw_wobbly_circle(draw, (cx + 30, cy - 260), 15, width=4)
            self._draw_wobbly_circle(draw, (cx, cy - 210 + mouth_offset), 20 + mouth_offset, width=5)
        elif pose == CharacterPose.SKEPTICAL:
            self._draw_wobbly_line(draw, (cx - 45, cy - 260), (cx - 15, cy - 255), width=6)
            self._draw_wobbly_line(draw, (cx + 15, cy - 265), (cx + 45, cy - 255), width=6)
            self._draw_wobbly_line(draw, (cx - 20, cy - 210), (cx + 20, cy - 210 + mouth_offset), width=5)
        else:
            draw.ellipse([cx - 35, cy - 265, cx - 15, cy - 245], fill=self.pen_color)
            draw.ellipse([cx + 15, cy - 265, cx + 35, cy - 245], fill=self.pen_color)
            if pose == CharacterPose.CELEBRATING or pose == CharacterPose.CONFIDENT:
                draw.arc([cx - 30, cy - 230, cx + 30, cy - 190 + mouth_offset], start=0, end=180, fill=self.pen_color, width=6)
            else:
                self._draw_wobbly_line(draw, (cx - 15, cy - 215), (cx + 15, cy - 215 + mouth_offset), width=5)

        self._draw_wobbly_line(draw, spine_top, spine_bottom, width=12)
        
        leg_l = (cx - 80, cy + 300)
        leg_r = (cx + 80, cy + 300)
        self._draw_wobbly_line(draw, spine_bottom, leg_l, width=12)
        self._draw_wobbly_line(draw, spine_bottom, leg_r, width=12)
        
        shoulder = (cx, cy - 120)
        
        # Arm swaying animation
        sway = math.sin(frame_idx * 0.15) * 20
        
        if pose == CharacterPose.CELEBRATING:
            self._draw_wobbly_line(draw, shoulder, (cx - 120 + sway, cy - 250), width=10)
            self._draw_wobbly_line(draw, shoulder, (cx + 120 + sway, cy - 250), width=10)
        elif pose == CharacterPose.THINKING:
            self._draw_wobbly_line(draw, shoulder, (cx - 100, cy - 50 + sway), width=10)
            elbow = (cx + 90, cy - 50)
            self._draw_wobbly_line(draw, shoulder, elbow, width=10)
            self._draw_wobbly_line(draw, elbow, (cx + 40, cy - 180 + (sway/2)), width=10)
        else:
            elbow_l = (cx - 100, cy - 20 + sway)
            elbow_r = (cx + 100, cy - 20 - sway)
            hip_l = (cx - 30, cy + 50)
            hip_r = (cx + 30, cy + 50)
            
            self._draw_wobbly_line(draw, shoulder, elbow_l, width=10)
            self._draw_wobbly_line(draw, elbow_l, hip_l, width=10)
            self._draw_wobbly_line(draw, shoulder, elbow_r, width=10)
            self._draw_wobbly_line(draw, elbow_r, hip_r, width=10)

    def _draw_handwritten_text(self, draw: ImageDraw.ImageDraw, text: str, cx: float, cy: float, max_width: int, progress: float):
        font = self._get_font(50)
        words = text.split()
        
        # Typewriter effect based on progress
        words_to_show = max(1, int(len(words) * progress))
        display_words = words[:words_to_show]
        
        lines = []
        current_line = []
        for w in display_words:
            current_line.append(w)
            test_line = " ".join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width:
                current_line.pop()
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [w]
        if current_line:
            lines.append(" ".join(current_line))

        line_height = 65
        total_text_height = len(lines) * line_height
        
        ty = cy - (total_text_height // 2)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            tx = cx - (line_w // 2)
            
            draw.text((tx, ty), line, fill=self.pen_color, font=font)
            ty += line_height

    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "whiteboard",
    ) -> List[VisualAsset]:
        
        visuals_dir = project_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        assets: List[VisualAsset] = []

        poses = [
            CharacterPose.CONFIDENT,
            CharacterPose.SKEPTICAL,
            CharacterPose.THINKING,
            CharacterPose.SHOCKED,
            CharacterPose.CELEBRATING,
        ]

        for idx, sc in enumerate(script.scenes):
            asset_id = f"asset_{idx+1:03d}"
            target_mp4 = visuals_dir / f"{asset_id}.mp4"
            pose = poses[idx % len(poses)]
            
            duration_sec = sc.duration_est
            if duration_sec <= 0:
                duration_sec = 3.0
                
            total_frames = int(duration_sec * self.fps)
            frames_dir = visuals_dir / f"frames_{asset_id}"
            frames_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Rendering {total_frames} animated stickman frames for scene {idx+1}...")
            
            # Render frames
            for frame_idx in range(total_frames):
                img = Image.new("RGB", (self.width, self.height), self.bg_color)
                draw = ImageDraw.Draw(img)

                # Draw stickman with animation frame
                self._draw_stickman(draw, self.width // 2, 1300, pose, frame_idx)

                # Draw typewriter text
                progress = min(1.0, (frame_idx / (total_frames * 0.7))) # Text finishes at 70% of scene
                text_to_draw = sc.narration
                self._draw_handwritten_text(draw, text_to_draw, self.width // 2, 500, 900, progress)

                frame_path = frames_dir / f"frame_{frame_idx:04d}.png"
                img.save(str(frame_path), quality=80)

            # Compile into MP4
            logger.info(f"Compiling frames to {target_mp4} using FFmpeg...")
            args = [
                "-y",
                "-framerate", str(self.fps),
                "-i", str(frames_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
            ]
            
            if settings.render_mode == "low_resource":
                args.extend(["-preset", "ultrafast", "-threads", "1"])
            else:
                args.extend(["-preset", "veryfast"])
                
            args.append(str(target_mp4))
            
            ret, _, err = ffmpeg_service.run_command(args, timeout=300)
            if ret != 0:
                raise RuntimeError(f"Failed to compile stickman frames into video: {err}")

            # Clean up frames to save disk space
            shutil.rmtree(frames_dir, ignore_errors=True)

            logger.info(f"Rendered Stickman animated scene {idx+1} -> {target_mp4}")

            assets.append(
                VisualAsset(
                    asset_id=asset_id,
                    file_path=str(target_mp4),
                    source_url="local://procedural/stickman_engine",
                    source_name="Procedural Stickman Engine (Animated)",
                    license="Original Copyright Free Channel Asset",
                    creator="Stickman Director",
                    attribution_required=False,
                    is_procedural=True,
                )
            )

        return assets
