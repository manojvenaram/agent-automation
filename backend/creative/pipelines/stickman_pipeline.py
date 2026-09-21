import math
import random
from typing import List, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.core.logging import logger
from backend.creative.cartoon_engine import CharacterPose

class StickmanPipeline(BaseRenderPipeline):
    """
    Procedurally renders Stickman animations with a hand-drawn whiteboard aesthetic.
    """
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.bg_color = (250, 250, 250) # Off-white whiteboard
        self.pen_color = (15, 15, 15)   # Almost black dry-erase marker

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

    def _draw_wobbly_line(self, draw: ImageDraw.ImageDraw, pt1: Tuple[int, int], pt2: Tuple[int, int], width: int = 8, wobble_amount: int = 4):
        """Draws a line broken into segments with random offsets to simulate a hand-drawn wobbly line."""
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
            # Add random wobble perpendicular to the line
            ox = random.randint(-wobble_amount, wobble_amount)
            oy = random.randint(-wobble_amount, wobble_amount)
            pts.append((int(cx + ox), int(cy + oy)))
            
        pts.append((x2, y2))
        
        # Draw the segmented line twice for a sketch effect
        draw.line(pts, fill=self.pen_color, width=width, joint="curve")
        
        # Draw a slightly thinner, offset line for the "dry erase" overlapping stroke look
        pts2 = [(p[0] + random.randint(-1, 1), p[1] + random.randint(-1, 1)) for p in pts]
        draw.line(pts2, fill=(40, 40, 40, 150), width=max(1, width - 2), joint="curve")

    def _draw_wobbly_circle(self, draw: ImageDraw.ImageDraw, center: Tuple[int, int], radius: int, width: int = 8):
        """Draws a sketchy, imperfect circle."""
        cx, cy = center
        segments = 36
        pts = []
        for i in range(segments + 2): # Overlap slightly
            angle = (i * 2 * math.pi) / segments
            # Add a slight warp to the radius for imperfection
            r = radius + random.randint(-3, 3)
            x = cx + int(r * math.cos(angle))
            y = cy + int(r * math.sin(angle))
            pts.append((x, y))
            
        draw.line(pts, fill=self.pen_color, width=width, joint="curve")

    def _draw_stickman(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, pose: CharacterPose):
        """Draws a stickman with a specific pose."""
        head_radius = 80
        head_center = (cx, cy - 250)
        
        # Head
        self._draw_wobbly_circle(draw, head_center, head_radius)
        
        # Spine
        spine_top = (cx, cy - 170)
        spine_bottom = (cx, cy + 100)
        
        # Eyes
        if pose == CharacterPose.SHOCKED:
            self._draw_wobbly_circle(draw, (cx - 30, cy - 260), 15, width=4)
            self._draw_wobbly_circle(draw, (cx + 30, cy - 260), 15, width=4)
            # Open mouth
            self._draw_wobbly_circle(draw, (cx, cy - 210), 20, width=5)
        elif pose == CharacterPose.SKEPTICAL:
            # Squinted eyes
            self._draw_wobbly_line(draw, (cx - 45, cy - 260), (cx - 15, cy - 255), width=6)
            self._draw_wobbly_line(draw, (cx + 15, cy - 265), (cx + 45, cy - 255), width=6)
            # Straight mouth
            self._draw_wobbly_line(draw, (cx - 20, cy - 210), (cx + 20, cy - 210), width=5)
        else:
            # Normal dot eyes
            draw.ellipse([cx - 35, cy - 265, cx - 15, cy - 245], fill=self.pen_color)
            draw.ellipse([cx + 15, cy - 265, cx + 35, cy - 245], fill=self.pen_color)
            if pose == CharacterPose.CELEBRATING or pose == CharacterPose.CONFIDENT:
                # Smile
                draw.arc([cx - 30, cy - 230, cx + 30, cy - 190], start=0, end=180, fill=self.pen_color, width=6)
            else:
                # Neutral mouth
                self._draw_wobbly_line(draw, (cx - 15, cy - 215), (cx + 15, cy - 215), width=5)

        # Draw spine
        self._draw_wobbly_line(draw, spine_top, spine_bottom, width=12)
        
        # Legs
        leg_l = (cx - 80, cy + 300)
        leg_r = (cx + 80, cy + 300)
        self._draw_wobbly_line(draw, spine_bottom, leg_l, width=12)
        self._draw_wobbly_line(draw, spine_bottom, leg_r, width=12)
        
        # Arms
        shoulder = (cx, cy - 120)
        if pose == CharacterPose.CELEBRATING:
            # Arms up
            self._draw_wobbly_line(draw, shoulder, (cx - 120, cy - 250), width=10)
            self._draw_wobbly_line(draw, shoulder, (cx + 120, cy - 250), width=10)
        elif pose == CharacterPose.THINKING:
            # One hand to chin
            self._draw_wobbly_line(draw, shoulder, (cx - 100, cy - 50), width=10) # Left arm resting down
            # Right arm bent to chin
            elbow = (cx + 90, cy - 50)
            self._draw_wobbly_line(draw, shoulder, elbow, width=10)
            self._draw_wobbly_line(draw, elbow, (cx + 40, cy - 180), width=10) # Hand near chin
        else: # CONFIDENT / SKEPTICAL / DEFAULT
            # Hands on hips
            elbow_l = (cx - 100, cy - 20)
            elbow_r = (cx + 100, cy - 20)
            hip_l = (cx - 30, cy + 50)
            hip_r = (cx + 30, cy + 50)
            
            self._draw_wobbly_line(draw, shoulder, elbow_l, width=10)
            self._draw_wobbly_line(draw, elbow_l, hip_l, width=10)
            
            self._draw_wobbly_line(draw, shoulder, elbow_r, width=10)
            self._draw_wobbly_line(draw, elbow_r, hip_r, width=10)

    def _draw_handwritten_text(self, draw: ImageDraw.ImageDraw, text: str, cx: int, cy: int, max_width: int):
        """Draws handwritten text with a slight rotation to look natural."""
        font = self._get_font(50)
        words = text.split()
        lines = []
        current_line = []
        for w in words:
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
            
            # Slight random tilt for handwriting
            temp_img = Image.new("RGBA", (line_w + 20, line_height + 20), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            temp_draw.text((10, 10), line, fill=self.pen_color, font=font)
            
            angle = random.uniform(-1.5, 1.5)
            rotated = temp_img.rotate(angle, resample=Image.BICUBIC, expand=1)
            
            draw._image.paste(rotated, (tx - 10, ty - 10), rotated)
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
            target_file = visuals_dir / f"{asset_id}.jpg"
            pose = poses[idx % len(poses)]
            
            # Create a blank whiteboard canvas
            img = Image.new("RGB", (self.width, self.height), self.bg_color)
            draw = ImageDraw.Draw(img)

            # Draw some faint whiteboard smudges/noise for realism
            for _ in range(5):
                sx = random.randint(0, self.width)
                sy = random.randint(0, self.height)
                draw.ellipse([sx, sy, sx + 200, sy + 200], fill=(240, 240, 240))

            # Draw the stickman at the bottom center
            self._draw_stickman(draw, self.width // 2, 1300, pose)

            # Draw the narrative text above the stickman
            text_to_draw = sc.narration[:100] + ("..." if len(sc.narration) > 100 else "")
            self._draw_handwritten_text(draw, text_to_draw, self.width // 2, 500, max_width=900)

            # Save the frame
            img.save(str(target_file), quality=90)
            logger.info(f"Rendered Stickman scene {idx+1} -> {target_file}")

            assets.append(
                VisualAsset(
                    asset_id=asset_id,
                    file_path=str(target_file),
                    source_url="local://procedural/stickman_engine",
                    source_name="Procedural Stickman Engine",
                    license="Original Copyright Free Channel Asset",
                    creator="Stickman Director",
                    attribution_required=False,
                    is_procedural=True,
                )
            )

        return assets
