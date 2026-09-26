import os
import asyncio
import edge_tts
from backend.core.logging import logger

class AudioGenerationEngine:
    def __init__(self):
        pass

    async def generate_voiceover_async(self, text: str, voice_id: str = "en-US-ChristopherNeural") -> str:
        """
        Converts the script into speech using edge-tts.
        """
        logger.info(f"Generating TTS for text length: {len(text)}")
        output_dir = os.path.join(os.getcwd(), "tmp", "generated_audio")
        os.makedirs(output_dir, exist_ok=True)
        
        simulated_output_path = os.path.join(output_dir, f"{hash(text)}.mp3")
        
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(simulated_output_path)
        
        logger.info(f"Audio generated at: {simulated_output_path}")
        return simulated_output_path

    def generate_voiceover(self, text: str, voice_id: str = "en-US-ChristopherNeural") -> str:
        return asyncio.run(self.generate_voiceover_async(text, voice_id))
