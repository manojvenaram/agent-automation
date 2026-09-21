import os
import random
from typing import List
from pathlib import Path
from playwright.sync_api import sync_playwright

from backend.models import ScriptModel, VisualAsset
from backend.creative.creative_director import CreativeDirection
from backend.creative.pipelines.base import BaseRenderPipeline
from backend.services.ffmpeg_service import ffmpeg_service
from backend.core.logging import logger

TWEET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { background-color: #000; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 1920px; width: 1080px; margin: 0; }
    .tweet-container { background-color: #15202B; border: 1px solid #38444D; border-radius: 30px; padding: 60px; width: 850px; }
    .header { display: flex; align-items: center; margin-bottom: 30px; }
    .avatar { width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(45deg, #1DA1F2, #1991DA); margin-right: 30px; }
    .name-block { display: flex; flex-direction: column; }
    .name { font-size: 42px; font-weight: bold; }
    .handle { font-size: 32px; color: #8899A6; margin-top: 5px; }
    .content { font-size: 55px; line-height: 1.4; margin-bottom: 40px; word-wrap: break-word; }
    .metrics { color: #8899A6; font-size: 32px; border-top: 1px solid #38444D; padding-top: 30px; }
</style>
</head>
<body>
    <div class="tweet-container">
        <div class="header">
            <div class="avatar"></div>
            <div class="name-block">
                <div class="name">AI Researcher</div>
                <div class="handle">@autonomous_ai</div>
            </div>
        </div>
        <div class="content">{text}</div>
        <div class="metrics">12.5K Retweets &nbsp;&nbsp; 45.2K Likes</div>
    </div>
</body>
</html>
"""

TERMINAL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { background-color: #1E1E1E; color: #D4D4D4; font-family: "Consolas", "Courier New", monospace; display: flex; justify-content: center; align-items: center; height: 1920px; width: 1080px; margin: 0; }
    .window { background-color: #252526; border-radius: 20px; width: 900px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); overflow: hidden; }
    .titlebar { background-color: #323233; height: 60px; display: flex; align-items: center; padding: 0 30px; }
    .dots { display: flex; gap: 15px; }
    .dot { width: 25px; height: 25px; border-radius: 50%; }
    .red { background-color: #FF5F56; }
    .yellow { background-color: #FFBD2E; }
    .green { background-color: #27C93F; }
    .content { padding: 60px; font-size: 45px; line-height: 1.6; }
    .prompt { color: #4AF626; font-weight: bold; }
    .cursor { display: inline-block; width: 25px; height: 50px; background-color: #D4D4D4; margin-left: 10px; vertical-align: middle; }
</style>
</head>
<body>
    <div class="window">
        <div class="titlebar">
            <div class="dots">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
            </div>
        </div>
        <div class="content">
            <span class="prompt">user@system:~$</span> execute analysis<br><br>
            {text}<span class="cursor"></span>
        </div>
    </div>
</body>
</html>
"""

class HyperframesPipeline(BaseRenderPipeline):
    """
    Renders pure HTML/CSS programmatic animations into video frames.
    Uses headless Chromium via Playwright.
    """
    
    def _render_html_to_image(self, html_content: str, output_path: str):
        """Uses Playwright to render HTML to a 1080x1920 screenshot."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.set_content(html_content)
            page.wait_for_load_state("networkidle")
            page.screenshot(path=output_path)
            browser.close()

    def render_assets(
        self,
        project_id: str,
        script: ScriptModel,
        project_dir: Path,
        direction: CreativeDirection,
        topic: str = "",
        aesthetic_style: str = "web",
    ) -> List[VisualAsset]:
        
        logger.info(f"[HyperframesPipeline] Rendering {len(script.scenes)} Web UI scenes via Playwright...")
        
        visuals_dir = project_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        
        assets: List[VisualAsset] = []
        
        # Decide template style based on category
        cat_lower = direction.format.value.lower()
        if "story" in cat_lower or "social" in cat_lower or "reddit" in cat_lower:
            template = TWEET_TEMPLATE
        elif "tech" in cat_lower or "code" in cat_lower or "hack" in cat_lower:
            template = TERMINAL_TEMPLATE
        else:
            template = TWEET_TEMPLATE

        for idx, scene in enumerate(script.scenes):
            asset_id = f"hyperframe_{idx+1:03d}"
            target_image = visuals_dir / f"{asset_id}.png"
            target_video = visuals_dir / f"{asset_id}.mp4"
            
            # 1. Inject text into HTML
            html_content = template.replace("{text}", scene.narration or "Processing data...")
            
            # 2. Render to PNG
            self._render_html_to_image(html_content, str(target_image))
            
            # 3. Animate the static PNG into a Ken Burns video clip
            # Using ffmpeg_service to give it a slow subtle zoom (like scrolling a webpage)
            final_clip_path = ffmpeg_service.create_still_scene_video(
                image_path=str(target_image),
                output_path=str(target_video),
                duration=scene.duration_est,
                zoom_direction=random.choice(["zoom_in", "zoom_out"])
            )
            
            assets.append(
                VisualAsset(
                    asset_id=asset_id,
                    file_path=final_clip_path,
                    source_url="local://hyperframes",
                    source_name="Playwright Hyperframes Engine",
                    license="Custom Proprietary",
                    creator="ShortsAgent",
                    attribution_required=False,
                    is_procedural=True,
                )
            )
            
        return assets
