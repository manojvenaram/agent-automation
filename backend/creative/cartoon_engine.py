"""
Cartoon Engine for YouTube Shorts.
Procedurally renders 1080x1920 (9:16) original cartoon artwork, characters,
and comic-strip scenes using Pillow.
100% original, copyright-safe, local generation ($0 API cost).

Supports recurring channel characters:
- "Byte": The overconfident, hyper-intelligent robot
- "Sam": The grounded, skeptical, witty human explorer
"""

import math
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from backend.core.logging import logger


class CharacterPose(str, Enum):
    CONFIDENT = "CONFIDENT"
    SKEPTICAL = "SKEPTICAL"
    SHOCKED = "SHOCKED"
    THINKING = "THINKING"
    CELEBRATING = "CELEBRATING"
    MALFUNCTION = "MALFUNCTION"


class CartoonEngine:
    def __init__(self):
        self.width = 1080
        self.height = 1920

    def _get_font(self, size: int) -> ImageFont.ImageFont:
        font_paths = [
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\segoeuib.ttf",
            "C:\\Windows\\Fonts\\impact.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        for p in font_paths:
            if Path(p).exists():
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _draw_vibrant_comic_background(self, draw: ImageDraw.ImageDraw, theme: str = "space") -> None:
        """Draws dynamic vertical gradient with comic burst or speed lines."""
        if theme == "cyber":
            c_top = (15, 23, 42)      # Deep slate
            c_bot = (6, 78, 59)       # Dark emerald
            accent = (52, 211, 153)   # Neon green
        elif theme == "comedy":
            c_top = (88, 28, 135)     # Purple
            c_bot = (194, 65, 12)     # Orange
            accent = (250, 204, 21)   # Yellow
        else:  # Space / Tech
            c_top = (10, 15, 30)      # Midnight navy
            c_bot = (30, 27, 75)      # Deep indigo
            accent = (56, 189, 248)   # Sky cyan

        # Vertical gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(c_top[0] * (1 - ratio) + c_bot[0] * ratio)
            g = int(c_top[1] * (1 - ratio) + c_bot[1] * ratio)
            b = int(c_top[2] * (1 - ratio) + c_bot[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Dynamic comic radial bursts
        cx, cy = self.width // 2, 850
        ray_count = 24
        for i in range(ray_count):
            if i % 2 == 0:
                angle1 = (2 * math.pi / ray_count) * i
                angle2 = (2 * math.pi / ray_count) * (i + 0.5)
                r_outer = 1200
                p1 = (cx, cy)
                p2 = (int(cx + r_outer * math.cos(angle1)), int(cy + r_outer * math.sin(angle1)))
                p3 = (int(cx + r_outer * math.cos(angle2)), int(cy + r_outer * math.sin(angle2)))
                draw.polygon([p1, p2, p3], fill=(*accent, 18))

    def _draw_byte_robot(
        self,
        draw: ImageDraw.ImageDraw,
        center_x: int,
        center_y: int,
        pose: CharacterPose,
    ) -> None:
        """Draws 'Byte' the overconfident robot with procedural geometry."""
        # Body colors
        robot_metal = (203, 213, 225)     # Chrome slate
        metal_shadow = (148, 163, 184)
        neon_cyan = (34, 211, 238)
        dark_visor = (15, 23, 42)

        # Antenna
        draw.line([(center_x, center_y - 200), (center_x, center_y - 280)], fill=robot_metal, width=12)
        tip_color = (239, 68, 68) if pose == CharacterPose.MALFUNCTION else neon_cyan
        draw.ellipse(
            [(center_x - 24, center_y - 328), (center_x + 24, center_y - 280)],
            fill=tip_color,
            outline=(255, 255, 255),
            width=4,
        )

        # Head chassis (rounded rectangular box)
        head_box = [center_x - 180, center_y - 210, center_x + 180, center_y + 10]
        draw.rounded_rectangle(head_box, radius=40, fill=robot_metal, outline=(255, 255, 255), width=6)

        # Ear bolts
        draw.rounded_rectangle([center_x - 205, center_y - 140, center_x - 180, center_y - 60], radius=10, fill=metal_shadow)
        draw.rounded_rectangle([center_x + 180, center_y - 140, center_x + 205, center_y - 60], radius=10, fill=metal_shadow)

        # Visor
        visor_box = [center_x - 145, center_y - 165, center_x + 145, center_y - 45]
        draw.rounded_rectangle(visor_box, radius=24, fill=dark_visor, outline=metal_shadow, width=4)

        # Visor expressions based on pose
        if pose == CharacterPose.MALFUNCTION:
            # Crossed out red error eyes
            draw.line([(center_x - 100, center_y - 130), (center_x - 60, center_y - 80)], fill=(239, 68, 68), width=8)
            draw.line([(center_x - 60, center_y - 130), (center_x - 100, center_y - 80)], fill=(239, 68, 68), width=8)
            draw.line([(center_x + 60, center_y - 130), (center_x + 100, center_y - 80)], fill=(239, 68, 68), width=8)
            draw.line([(center_x + 100, center_y - 130), (center_x + 60, center_y - 80)], fill=(239, 68, 68), width=8)
        elif pose == CharacterPose.SKEPTICAL:
            # One squinting eye, one normal raised eye
            draw.line([(center_x - 100, center_y - 105), (center_x - 50, center_y - 105)], fill=neon_cyan, width=12)
            draw.ellipse([(center_x + 60, center_y - 125), (center_x + 95, center_y - 85)], fill=neon_cyan)
        elif pose == CharacterPose.SHOCKED:
            # Massive wide glowing circles
            draw.ellipse([(center_x - 110, center_y - 140), (center_x - 45, center_y - 70)], fill=neon_cyan)
            draw.ellipse([(center_x + 45, center_y - 140), (center_x + 110, center_y - 70)], fill=neon_cyan)
        else:  # CONFIDENT / CELEBRATING / THINKING
            # Bright cyan glowing eyes
            draw.rounded_rectangle([center_x - 105, center_y - 125, center_x - 45, center_y - 85], radius=12, fill=neon_cyan)
            draw.rounded_rectangle([center_x + 45, center_y - 125, center_x + 105, center_y - 85], radius=12, fill=neon_cyan)

        # Mouth / speaker grill
        if pose == CharacterPose.CONFIDENT or pose == CharacterPose.CELEBRATING:
            draw.arc([center_x - 50, center_y - 35, center_x + 50, center_y + 0], start=0, end=180, fill=(71, 85, 105), width=6)
        else:
            draw.line([(center_x - 40, center_y - 15), (center_x + 40, center_y - 15)], fill=(71, 85, 105), width=6)

        # Body torso
        body_box = [center_x - 140, center_y + 25, center_x + 140, center_y + 360]
        draw.rounded_rectangle(body_box, radius=35, fill=robot_metal, outline=(255, 255, 255), width=6)

        # Glowing chest core
        core_color = (239, 68, 68) if pose == CharacterPose.MALFUNCTION else neon_cyan
        draw.ellipse([(center_x - 45, center_y + 80), (center_x + 45, center_y + 170)], fill=core_color, outline=(255, 255, 255), width=4)

        # Arms
        if pose == CharacterPose.CELEBRATING:
            # Arms up in air
            draw.line([(center_x - 140, center_y + 70), (center_x - 240, center_y - 70)], fill=robot_metal, width=28)
            draw.ellipse([(center_x - 265, center_y - 100), (center_x - 215, center_y - 45)], fill=metal_shadow)
            draw.line([(center_x + 140, center_y + 70), (center_x + 240, center_y - 70)], fill=robot_metal, width=28)
            draw.ellipse([(center_x + 215, center_y - 100), (center_x + 265, center_y - 45)], fill=metal_shadow)
        elif pose == CharacterPose.THINKING:
            # One hand to chin
            draw.line([(center_x + 140, center_y + 70), (center_x + 170, center_y + 10)], fill=robot_metal, width=28)
            draw.line([(center_x - 140, center_y + 70), (center_x - 190, center_y + 220)], fill=robot_metal, width=28)
        else:
            # Standard hands on hips / relaxed
            draw.line([(center_x - 140, center_y + 70), (center_x - 210, center_y + 180)], fill=robot_metal, width=28)
            draw.line([(center_x + 140, center_y + 70), (center_x + 210, center_y + 180)], fill=robot_metal, width=28)

    def _draw_sam_human(
        self,
        draw: ImageDraw.ImageDraw,
        center_x: int,
        center_y: int,
        pose: CharacterPose,
    ) -> None:
        """Draws 'Sam' the skeptical human explorer with stylized cartoon shapes."""
        skin_tone = (253, 224, 185)
        hoodie_color = (225, 29, 72)     # Crimson / Rose
        hoodie_dark = (159, 18, 57)
        hair_color = (68, 64, 60)         # Charcoal brown
        cap_color = (245, 158, 11)        # Vibrant amber

        # Hair / Cap back
        draw.ellipse([(center_x - 140, center_y - 230), (center_x + 140, center_y + 10)], fill=hair_color)

        # Face
        draw.ellipse([(center_x - 120, center_y - 180), (center_x + 120, center_y + 20)], fill=skin_tone, outline=(30, 41, 59), width=5)

        # Amber backwards baseball cap
        draw.arc([center_x - 130, center_y - 240, center_x + 130, center_y - 60], start=180, end=360, fill=cap_color, width=32)
        draw.polygon([(center_x + 70, center_y - 160), (center_x + 165, center_y - 185), (center_x + 130, center_y - 130)], fill=cap_color)

        # Eyes
        if pose == CharacterPose.SHOCKED:
            draw.ellipse([(center_x - 70, center_y - 95), (center_x - 20, center_y - 45)], fill=(255, 255, 255), outline=(0, 0, 0), width=4)
            draw.ellipse([(center_x + 20, center_y - 95), (center_x + 70, center_y - 45)], fill=(255, 255, 255), outline=(0, 0, 0), width=4)
            draw.ellipse([(center_x - 52, center_y - 75), (center_x - 38, center_y - 61)], fill=(0, 0, 0))
            draw.ellipse([(center_x + 38, center_y - 75), (center_x + 52, center_y - 61)], fill=(0, 0, 0))
        elif pose == CharacterPose.SKEPTICAL:
            # One eye squinting, one raised
            draw.line([(center_x - 70, center_y - 110), (center_x - 20, center_y - 125)], fill=(0, 0, 0), width=7)  # Raised brow
            draw.ellipse([(center_x - 65, center_y - 95), (center_x - 25, center_y - 55)], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
            draw.ellipse([(center_x - 50, center_y - 80), (center_x - 38, center_y - 68)], fill=(0, 0, 0))
            # Squinted eye
            draw.line([(center_x + 20, center_y - 105), (center_x + 65, center_y - 105)], fill=(0, 0, 0), width=5)
            draw.line([(center_x + 20, center_y - 75), (center_x + 65, center_y - 75)], fill=(0, 0, 0), width=6)
        else:
            # Standard expressive cartoon eyes
            draw.ellipse([(center_x - 65, center_y - 90), (center_x - 25, center_y - 50)], fill=(255, 255, 255), outline=(0, 0, 0), width=4)
            draw.ellipse([(center_x + 25, center_y - 90), (center_x + 65, center_y - 50)], fill=(255, 255, 255), outline=(0, 0, 0), width=4)
            draw.ellipse([(center_x - 50, center_y - 75), (center_x - 38, center_y - 63)], fill=(0, 0, 0))
            draw.ellipse([(center_x + 40, center_y - 75), (center_x + 52, center_y - 63)], fill=(0, 0, 0))

        # Mouth
        if pose == CharacterPose.SHOCKED:
            draw.ellipse([(center_x - 25, center_y - 15), (center_x + 25, center_y + 15)], fill=(239, 68, 68), outline=(0, 0, 0), width=3)
        elif pose == CharacterPose.SKEPTICAL:
            draw.line([(center_x - 30, center_y), (center_x + 30, center_y - 10)], fill=(0, 0, 0), width=5)
        else:
            draw.arc([center_x - 35, center_y - 15, center_x + 35, center_y + 10], start=0, end=180, fill=(0, 0, 0), width=5)

        # Hoodie Torso
        torso_box = [center_x - 150, center_y + 35, center_x + 150, center_y + 380]
        draw.rounded_rectangle(torso_box, radius=40, fill=hoodie_color, outline=(255, 255, 255), width=6)

        # Hoodie drawstrings
        draw.line([(center_x - 30, center_y + 45), (center_x - 30, center_y + 140)], fill=(255, 255, 255), width=6)
        draw.line([(center_x + 30, center_y + 45), (center_x + 30, center_y + 140)], fill=(255, 255, 255), width=6)

        # Arms
        if pose == CharacterPose.MALFUNCTION:
            # Facepalm pose
            draw.line([(center_x - 140, center_y + 90), (center_x - 10, center_y - 60)], fill=hoodie_dark, width=32)
            draw.ellipse([(center_x - 30, center_y - 80), (center_x + 10, center_y - 40)], fill=skin_tone)
        elif pose == CharacterPose.THINKING:
            draw.line([(center_x + 140, center_y + 90), (center_x + 20, center_y - 10)], fill=hoodie_dark, width=30)
            draw.ellipse([(center_x + 5, center_y - 30), (center_x + 40, center_y + 5)], fill=skin_tone)
        else:
            draw.line([(center_x - 140, center_y + 90), (center_x - 220, center_y + 200)], fill=hoodie_dark, width=30)
            draw.line([(center_x + 140, center_y + 90), (center_x + 220, center_y + 200)], fill=hoodie_dark, width=30)

    def _draw_comic_speech_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        speaker_x: int,
        speaker_y: int,
        top_y: int = 150,
    ) -> None:
        """Draws a bold comic speech balloon with text."""
        font = self._get_font(46)
        # Wrap text
        words = text.split()
        lines = []
        current_line = []
        for w in words:
            current_line.append(w)
            test_line = " ".join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > 760:
                current_line.pop()
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [w]
        if current_line:
            lines.append(" ".join(current_line))

        line_height = 58
        total_text_height = len(lines) * line_height
        bubble_h = total_text_height + 70
        bubble_w = 880
        bubble_left = (self.width - bubble_w) // 2
        bubble_top = top_y
        bubble_bottom = bubble_top + bubble_h

        # Bubble background
        bubble_box = [bubble_left, bubble_top, bubble_left + bubble_w, bubble_bottom]
        draw.rounded_rectangle(bubble_box, radius=35, fill=(255, 255, 255), outline=(15, 23, 42), width=7)

        # Bubble pointer towards speaker
        pointer = [
            (bubble_left + bubble_w // 2 - 25, bubble_bottom),
            (bubble_left + bubble_w // 2 + 25, bubble_bottom),
            (speaker_x, speaker_y - 220),
        ]
        draw.polygon(pointer, fill=(255, 255, 255), outline=(15, 23, 42))
        # Re-cover seam
        draw.line([pointer[0], pointer[1]], fill=(255, 255, 255), width=6)

        # Draw lines of text
        ty = bubble_top + 35
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            tx = (self.width - line_w) // 2
            draw.text((tx, ty), line, fill=(15, 23, 42), font=font)
            ty += line_height

    def render_scene(
        self,
        character_name: str,
        pose: CharacterPose,
        caption_title: str,
        dialogue: str,
        output_path: Path,
        theme: str = "space",
    ) -> Path:
        """
        Renders a full 1080x1920 9:16 vertical cartoon frame.
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        # Background
        self._draw_vibrant_comic_background(draw, theme=theme)

        # Title / Banner at the top
        banner_font = self._get_font(60)
        banner_bbox = draw.textbbox((0, 0), caption_title.upper(), font=banner_font)
        bw = banner_bbox[2] - banner_bbox[0] + 60
        bx = (self.width - bw) // 2
        draw.rounded_rectangle([bx, 60, bx + bw, 140], radius=20, fill=(250, 204, 21), outline=(0, 0, 0), width=5)
        draw.text(((self.width - (banner_bbox[2] - banner_bbox[0])) // 2, 70), caption_title.upper(), fill=(0, 0, 0), font=banner_font)

        # Character center position
        cx = self.width // 2
        cy = 1180

        # Draw character
        is_byte = "byte" in character_name.lower() or "robot" in character_name.lower()
        if is_byte:
            self._draw_byte_robot(draw, cx, cy, pose)
        else:
            self._draw_sam_human(draw, cx, cy, pose)

        # Dialogue speech balloon
        if dialogue:
            self._draw_comic_speech_bubble(draw, dialogue, cx, cy, top_y=190)

        # Save image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img_rgb = img.convert("RGB")
        img_rgb.save(str(output_path), quality=95)
        logger.info(f"Rendered cartoon scene ({character_name}, {pose.value}) -> {output_path}")
        return output_path

    def render_duo_scene(
        self,
        pose_byte: CharacterPose,
        pose_sam: CharacterPose,
        dialogue: str,
        speaking_char: str,
        output_path: Path,
        caption_title: str = "BYTE & SAM",
    ) -> Path:
        """
        Renders both Byte and Sam side-by-side in a two-shot comedy scene.
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        self._draw_vibrant_comic_background(draw, theme="comedy")

        # Top title banner
        banner_font = self._get_font(56)
        banner_bbox = draw.textbbox((0, 0), caption_title.upper(), font=banner_font)
        bw = banner_bbox[2] - banner_bbox[0] + 60
        bx = (self.width - bw) // 2
        draw.rounded_rectangle([bx, 60, bx + bw, 135], radius=18, fill=(250, 204, 21), outline=(0, 0, 0), width=5)
        draw.text(((self.width - (banner_bbox[2] - banner_bbox[0])) // 2, 70), caption_title.upper(), fill=(0, 0, 0), font=banner_font)

        # Place Byte on left, Sam on right
        byte_x = 320
        sam_x = 760
        char_y = 1260

        self._draw_byte_robot(draw, byte_x, char_y, pose_byte)
        self._draw_sam_human(draw, sam_x, char_y, pose_sam)

        # Speech bubble targeting the active speaker
        speaker_x = byte_x if "byte" in speaking_char.lower() else sam_x
        if dialogue:
            self._draw_comic_speech_bubble(draw, dialogue, speaker_x, char_y, top_y=180)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img_rgb = img.convert("RGB")
        img_rgb.save(str(output_path), quality=95)
        logger.info(f"Rendered duo cartoon scene ({caption_title}) -> {output_path}")
        return output_path


cartoon_engine = CartoonEngine()
