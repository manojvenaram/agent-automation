"""
FFmpeg Service for YouTube Shorts Video & Audio Processing.
Automatically locates standalone or system FFmpeg, validates media streams,
and constructs high-quality 9:16 compositions with Ken Burns motion,
subtitles burn-in, and audio ducking.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from backend.core.config import settings
from backend.core.logging import logger


class FFmpegService:
    def __init__(self):
        self._ffmpeg_bin = self._find_ffmpeg()
        logger.info(f"FFmpeg binary resolved: {self._ffmpeg_bin}")

    def _find_ffmpeg(self) -> str:
        """Locate FFmpeg binary from imageio-ffmpeg, system PATH, or environment."""
        # 1. Check if imageio_ffmpeg is installed and provides binary
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.exists(exe):
                return str(exe)
        except Exception:
            pass

        # 2. Check system PATH
        path_bin = shutil.which("ffmpeg")
        if path_bin:
            return path_bin

        # 3. Check common Windows installation paths
        common_paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ffmpeg" / "bin" / "ffmpeg.exe",
            Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/ffmpeg/bin/ffmpeg.exe"),
        ]
        for p in common_paths:
            if p.exists():
                return str(p)

        raise RuntimeError("FFmpeg executable not found. Please install imageio-ffmpeg or add ffmpeg to PATH.")

    @property
    def ffmpeg_path(self) -> str:
        return self._ffmpeg_bin

    def run_command(self, args: List[str], timeout: int = 180) -> Tuple[int, str, str]:
        """Execute an FFmpeg command safely, capturing stdout and stderr."""
        cmd = [self._ffmpeg_bin] + args
        logger.debug(f"Running FFmpeg: {' '.join(cmd[:8])}...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(f"FFmpeg command timed out after {timeout}s")
            raise TimeoutError(f"FFmpeg process exceeded {timeout}s timeout")

    def probe_file(self, file_path: str) -> Dict[str, Any]:
        """Inspect media file streams, duration, resolution, codecs using FFmpeg."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")

        # Use ffmpeg -i to probe media
        args = ["-i", file_path, "-hide_banner"]
        returncode, stdout, stderr = self.run_command(args, timeout=20)
        
        info = {
            "file_size": os.path.getsize(file_path),
            "has_video": False,
            "has_audio": False,
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "video_codec": "",
            "audio_codec": "",
        }

        # Parse stderr output from ffmpeg
        for line in stderr.splitlines():
            line_str = line.strip()
            # Duration: 00:00:32.45, start: ...
            if "Duration:" in line_str:
                parts = line_str.split("Duration:")[1].split(",")[0].strip()
                try:
                    h, m, s = parts.split(":")
                    info["duration"] = float(h) * 3600 + float(m) * 60 + float(s)
                except Exception:
                    pass
            # Stream #0:0(und): Video: h264 (...), 1080x1920 [SAR 1:1 DAR 9:16], 30 fps
            if "Video:" in line_str:
                info["has_video"] = True
                try:
                    parts = line_str.split("Video:")[1].split(",")
                    info["video_codec"] = parts[0].strip().split()[0]
                    for p in parts:
                        if "x" in p and any(c.isdigit() for c in p):
                            dim_candidate = p.strip().split()[0]
                            if "x" in dim_candidate:
                                w_str, h_str = dim_candidate.split("x")[:2]
                                if w_str.isdigit() and h_str.isdigit():
                                    info["width"] = int(w_str)
                                    info["height"] = int(h_str)
                        if "fps" in p:
                            fps_cand = p.strip().split()[0]
                            try:
                                info["fps"] = float(fps_cand)
                            except ValueError:
                                pass
                except Exception:
                    pass
            # Stream #0:1(und): Audio: aac (...), 44100 Hz, stereo
            if "Audio:" in line_str:
                info["has_audio"] = True
                try:
                    info["audio_codec"] = line_str.split("Audio:")[1].split(",")[0].strip().split()[0]
                except Exception:
                    pass

        return info

    def create_still_scene_video(
        self,
        image_path: str,
        output_path: str,
        duration: float,
        zoom_direction: str = "in",
    ) -> str:
        """
        Create a 1080x1920 30FPS MP4 video clip from a still image with Ken Burns pan/zoom effect.
        """
        out_dir = Path(output_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        frames = int(duration * settings.video_fps)
        w = settings.video_width
        h = settings.video_height

        import random
        effect = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
        if effect == "zoom_in":
            zoom_expr = f"1.0+0.15*(on/{frames})"
            x_expr, y_expr = "'iw/2-(iw/zoom/2)'", "'ih/2-(ih/zoom/2)'"
        elif effect == "zoom_out":
            zoom_expr = f"1.15-0.15*(on/{frames})"
            x_expr, y_expr = "'iw/2-(iw/zoom/2)'", "'ih/2-(ih/zoom/2)'"
        elif effect == "pan_left":
            zoom_expr = "1.15"
            x_expr = f"'(iw-iw/zoom/2)-(on/{frames})*(iw-iw/zoom)'"
            y_expr = "'ih/2-(ih/zoom/2)'"
        else: # pan_right
            zoom_expr = "1.15"
            x_expr = f"'(iw/zoom/2)+(on/{frames})*(iw-iw/zoom)'"
            y_expr = "'ih/2-(ih/zoom/2)'"

        # Filtergraph: zoompan directly on the 1080x1920 image
        vf = (
            f"zoompan=z='{zoom_expr}':d={frames}:"
            f"x={x_expr}:y={y_expr}:s={w}x{h}:fps={settings.video_fps},"
            f"format=yuv420p"
        )

        args = [
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", vf,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
        ]
        if settings.render_mode == "low_resource":
            args.extend(["-preset", "ultrafast", "-threads", "1"])
        else:
            args.extend(["-preset", "veryfast"])
            
        args.append(output_path)

        ret, stdout, stderr = self.run_command(args, timeout=120)
        if ret != 0:
            logger.warning(f"Ken Burns zoompan failed, falling back to static 9:16 scale: {stderr[:200]}")
            # Fallback simple scale & crop to 9:16
            simple_vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p"
            args_fb = [
                "-y",
                "-loop", "1",
                "-i", image_path,
                "-vf", simple_vf,
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                output_path,
            ]
            ret_fb, _, stderr_fb = self.run_command(args_fb, timeout=60)
            if ret_fb != 0:
                raise RuntimeError(f"Failed to render scene video: {stderr_fb}")

        return output_path

    def concatenate_scenes(
        self,
        scene_video_paths: List[str],
        output_path: str,
    ) -> str:
        """Concatenate multiple scene video files into one video."""
        out_dir = Path(output_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        concat_list_file = out_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for vp in scene_video_paths:
                # Escape backslashes for ffmpeg concat demuxer
                clean_path = str(Path(vp).resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        args = [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
        ]
        if settings.render_mode == "low_resource":
            args.extend(["-preset", "ultrafast", "-threads", "1"])
        else:
            args.extend(["-preset", "veryfast"])
            
        args.append(output_path)

        ret, stdout, stderr = self.run_command(args, timeout=180)
        if ret != 0:
            raise RuntimeError(f"FFmpeg scene concatenation failed: {stderr}")

        if concat_list_file.exists():
            concat_list_file.unlink()

        return output_path

    def composite_final_short(
        self,
        video_input: str,
        voiceover_audio: str,
        output_path: str,
        subtitles_file: Optional[str] = None,
        background_music: Optional[str] = None,
        music_volume: float = 0.10,
    ) -> str:
        """
        Merge video, narration audio, background music (ducked), and burn-in subtitles.
        Outputs a YouTube Shorts compliant 9:16 1080x1920 MP4 file.
        """
        out_dir = Path(output_path).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        # Probe voiceover duration
        v_info = self.probe_file(voiceover_audio)
        total_duration = v_info["duration"]
        if total_duration <= 0:
            total_duration = 30.0

        # Build FFmpeg command inputs
        args = ["-y", "-i", video_input, "-i", voiceover_audio]

        # Add procedural SFX input (Index 2)
        args.extend(["-f", "lavfi", "-i", "anoisesrc=d=1.5:c=pink,afade=t=out:d=1.5,volume=0.25"])

        filter_complex = []
        audio_out_label = "[aout]"

        if background_music and os.path.exists(background_music):
            args.extend(["-stream_loop", "-1", "-i", background_music]) # Index 3
            # Amix all 3: Voice (1), SFX (2), Music (3)
            filter_complex.append(f"[3:a]volume={music_volume}[bgm];[1:a][2:a][bgm]amix=inputs=3:duration=first:dropout_transition=2{audio_out_label}")
        else:
            # Amix Voice (1) and SFX (2)
            filter_complex.append(f"[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=2{audio_out_label}")

        # Video filter for subtitles
        video_map_label = "0:v"
        if subtitles_file and os.path.exists(subtitles_file):
            # Clean path with escaped colons and slashes for subtitles filter
            sub_escaped = str(Path(subtitles_file).resolve()).replace("\\", "/").replace(":", "\\:")
            filter_complex.append(f"[{video_map_label}]subtitles=filename='{sub_escaped}'[vout]")
            video_out_label = "[vout]"
        else:
            video_out_label = f"[{video_map_label}]"

        if filter_complex:
            args.extend(["-filter_complex", ";".join(filter_complex)])
            args.extend(["-map", video_out_label, "-map", audio_out_label])
        else:
            args.extend(["-map", "0:v", "-map", "1:a"])

        # Trim output strictly to narration duration
        args.extend([
            "-t", f"{total_duration:.3f}",
            "-c:v", "libx264",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
        ])
        if settings.render_mode == "low_resource":
            args.extend(["-preset", "ultrafast", "-threads", "1"])
        else:
            args.extend(["-preset", "veryfast"])
            
        args.append(output_path)

        ret, stdout, stderr = self.run_command(args, timeout=240)
        if ret != 0:
            logger.warning(f"Composite with subtitles filter failed, retrying without subtitle filter: {stderr[:200]}")
            # Fallback without subtitles burn-in if subtitles filter had font issue
            fb_args = [
                "-y",
                "-i", video_input,
                "-i", voiceover_audio,
                "-t", f"{total_duration:.3f}",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                output_path,
            ]
            fb_ret, _, fb_err = self.run_command(fb_args, timeout=120)
            if fb_ret != 0:
                raise RuntimeError(f"FFmpeg composition failed: {fb_err}")

        return output_path


# Global singleton
ffmpeg_service = FFmpegService()
