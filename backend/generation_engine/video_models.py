import os
import urllib.parse
import urllib.request
from backend.core.logging import logger
from moviepy.editor import ImageClip

class VideoGenerationEngine:
    """
    Interfaces with various video and image generation models.
    """
    def __init__(self):
        self.api_key = os.getenv("VIDEO_API_KEY")

    def generate_broll(self, prompt: str, duration: int = 3) -> str:
        """
        Takes a cinematic prompt and returns a path to the generated MP4.
        Uses a free Text-to-Image API (Pollinations.ai) to generate a real AI image,
        and converts it into a video clip.
        """
        logger.info(f"Generating {duration}s video for prompt: {prompt}")
        output_dir = os.path.join(os.getcwd(), "tmp", "generated_clips")
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean up prompt for the URL
        safe_prompt = urllib.parse.quote(prompt)
        # We request a 1080x1920 vertical image suitable for Shorts
        image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
        
        image_path = os.path.join(output_dir, f"{hash(prompt)}.jpg")
        simulated_output_path = os.path.join(output_dir, f"{hash(prompt)}.mp4")
        
        try:
            # 1. Download the generated AI image
            logger.info(f"Downloading AI image from {image_url}")
            urllib.request.urlretrieve(image_url, image_path)
            
            # 2. Convert the image into a video clip
            logger.info("Converting image to video clip...")
            clip = ImageClip(image_path).set_duration(duration)
            clip.write_videofile(simulated_output_path, fps=24, logger=None)
            clip.close()
            
            # Clean up the temp image
            if os.path.exists(image_path):
                os.remove(image_path)
                
            logger.info(f"Video generated at: {simulated_output_path}")
            return simulated_output_path
            
        except Exception as e:
            logger.error(f"Failed to generate real AI video: {e}")
            # Fallback to the solid color clip if API fails
            from moviepy.editor import ColorClip
            import random
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            clip = ColorClip(size=(1080, 1920), color=color, duration=duration)
            clip.write_videofile(simulated_output_path, fps=24, logger=None)
            clip.close()
            return simulated_output_path
