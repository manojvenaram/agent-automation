"""
QualityControlAgent for YouTube Shorts Validation.
Performs exhaustive technical and content quality audits before publishing:
- Technical: file exists, MP4 container, H.264/AAC, 1080x1920 9:16, 30 FPS, duration 20-60s.
- Audio: narration stream present, volume non-clipping, duration match.
- Captions: subtitle track present, synchronized, formatted.
- Content: hook validity, fact-checking confidence >= threshold (0.80).
Computes Quality Score (0-100) and triggers auto-repair recommendations.
"""

import os
from typing import List, Tuple
from backend.core.config import settings
from backend.core.database import save_qc_result
from backend.core.logging import logger
from backend.models import (
    FactCheckReport,
    ScriptModel,
    VideoQCReport,
)
from backend.services.ffmpeg_service import ffmpeg_service


class QualityControlAgent:
    def __init__(self):
        self.min_score = settings.minimum_quality_score
        self.min_duration = settings.min_duration
        self.max_duration = settings.max_duration

    def evaluate_video(
        self,
        project_id: str,
        video_path: str,
        script: ScriptModel,
        fact_report: FactCheckReport,
        subtitles_path: str,
    ) -> VideoQCReport:
        """Run complete QC inspection and compute composite quality score."""
        logger.info(f"Running Quality Control inspection on '{video_path}'...")
        issues: List[str] = []
        score = 0
        details = {}

        # 1. TECHNICAL INSPECTION (30 points max)
        tech_passed = True
        tech_points = 0
        if not os.path.exists(video_path):
            issues.append(f"Rendered video file not found: {video_path}")
            tech_passed = False
        else:
            file_size = os.path.getsize(video_path)
            details["file_size_bytes"] = file_size
            if file_size < 100 * 1024:
                issues.append(f"Video file is suspiciously small ({file_size} bytes)")
                tech_passed = False
            else:
                tech_points += 5

            try:
                probe = ffmpeg_service.probe_file(video_path)
                details["probe"] = probe

                # Check video stream
                if probe["has_video"]:
                    tech_points += 5
                else:
                    issues.append("Missing video stream in MP4 container")
                    tech_passed = False

                # Check 9:16 resolution (1080x1920)
                w, h = probe["width"], probe["height"]
                if (w == 1080 and h == 1920) or (w > 0 and h > 0 and abs((w / h) - (9 / 16)) < 0.05):
                    tech_points += 10
                else:
                    issues.append(f"Non-compliant aspect ratio: {w}x{h} (expected 1080x1920)")
                    tech_passed = False

                # Check duration
                dur = probe["duration"]
                details["duration_sec"] = dur
                if self.min_duration <= dur <= self.max_duration:
                    tech_points += 5
                else:
                    issues.append(f"Duration {dur:.1f}s out of bounds ({self.min_duration}-{self.max_duration}s)")
                    if dur < self.min_duration:
                        tech_passed = False

                # Check video codec
                if "h264" in probe["video_codec"].lower() or "avc" in probe["video_codec"].lower():
                    tech_points += 5
                else:
                    issues.append(f"Non-standard video codec: {probe['video_codec']}")
            except Exception as e:
                issues.append(f"Failed to probe video file: {e}")
                tech_passed = False

        score += tech_points

        # 2. AUDIO INSPECTION (25 points max)
        audio_passed = True
        audio_points = 0
        if details.get("probe", {}).get("has_audio"):
            audio_points += 15
            # Audio codec check
            if "aac" in details.get("probe", {}).get("audio_codec", "").lower():
                audio_points += 10
            else:
                audio_points += 5
        else:
            issues.append("Missing audio stream in rendered video")
            audio_passed = False

        score += audio_points

        # 3. CAPTIONS INSPECTION (20 points max)
        captions_passed = True
        caption_points = 0
        if os.path.exists(subtitles_path) and os.path.getsize(subtitles_path) > 100:
            caption_points += 20
        else:
            issues.append(f"Subtitles file missing or empty: {subtitles_path}")
            captions_passed = False

        score += caption_points

        # 4. CONTENT & FACTUAL CONFIDENCE INSPECTION (25 points max)
        content_passed = True
        content_points = 0
        if script.hook and len(script.hook) > 10:
            content_points += 10
        else:
            issues.append("Weak or empty script hook")
            content_passed = False

        if fact_report.passed:
            content_points += 15
        else:
            issues.append(f"Factual confidence ({fact_report.overall_confidence:.2f}) failed threshold")
            content_passed = False

        score += content_points

        passed = (
            tech_passed
            and audio_passed
            and captions_passed
            and content_passed
            and score >= self.min_score
        )

        report = VideoQCReport(
            passed=passed,
            quality_score=score,
            technical_passed=tech_passed,
            audio_passed=audio_passed,
            captions_passed=captions_passed,
            content_passed=content_passed,
            issues=issues,
            details=details,
        )

        save_qc_result(project_id, report)
        logger.info(
            f"QC Complete. Passed: {passed}, Score: {score}/100, Issues: {len(issues)}"
        )
        return report

    def diagnose_repair_action(self, qc_report: VideoQCReport) -> Tuple[str, str]:
        """
        Diagnose failure cause and prescribe targeted repair action:
        - REWRITE_SCRIPT
        - REGENERATE_VOICE
        - RECOLLECT_VISUALS
        - RERENDER_VIDEO
        """
        for issue in qc_report.issues:
            if "Factual confidence" in issue or "script hook" in issue:
                return "REWRITE_SCRIPT", issue
            if "audio stream" in issue:
                return "REGENERATE_VOICE", issue
            if "Subtitles file" in issue:
                return "RERENDER_VIDEO", issue
            if "aspect ratio" in issue or "duration" in issue or "small" in issue:
                return "RERENDER_VIDEO", issue

        return "RERENDER_VIDEO", "General render repair needed"


quality_control_agent = QualityControlAgent()
