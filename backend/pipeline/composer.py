import os
from typing import List
from backend.core.logging import logger
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

class VideoComposer:
    def __init__(self):
        pass

    def assemble_final_video(self, video_clips: List[str], audio_track: str, output_path: str) -> str:
        """
        Stitches the video clips together and adds the audio track.
        """
        logger.info(f"Starting video assembly. Clips: {len(video_clips)}, Audio: {audio_track}")
        
        try:
            # Load video clips
            clips = [VideoFileClip(clip) for clip in video_clips]
            
            # Concatenate videos
            final_video = concatenate_videoclips(clips)
            
            # Load audio and set it to the final video
            audio = AudioFileClip(audio_track)
            
            # Ensure the video is at least as long as the audio (or loop video if needed)
            # For simplicity, we just set the audio.
            final_video = final_video.set_audio(audio)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write the result to a file
            logger.info("Rendering final video...")
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                fps=24,
                logger=None
            )
            
            # Close clips to free resources
            for clip in clips:
                clip.close()
            audio.close()
            final_video.close()
                
            logger.info(f"Final video rendered successfully to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to assemble video: {e}")
            raise
