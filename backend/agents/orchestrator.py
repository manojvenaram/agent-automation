"""
Multi-Agent Orchestrator.
Manages the conversation between Director, ScriptWriter, FactChecker, and VideoPrompt agents.
Integrates basic token optimization to summarize history.
"""

from typing import List, Dict, Any, Optional
from backend.services.llm_service import LLMService
from backend.core.logging import logger

class Agent:
    def __init__(self, name: str, role: str, system_prompt: str, llm_service: LLMService):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm_service

    def generate_reply(self, message: str, context_history: str = "") -> str:
        prompt = (
            f"System: {self.system_prompt}\n\n"
            f"Context History:\n{context_history}\n\n"
            f"New Message:\n{message}\n\n"
            f"Respond as {self.name}:"
        )
        try:
            return self.llm.generate(prompt=prompt, system_prompt=self.system_prompt)
        except Exception as e:
            logger.error(f"Agent {self.name} failed to generate reply: {e}")
            return f"[Agent {self.name} failed to respond]"


class MultiAgentOrchestrator:
    def __init__(self):
        self.llm = LLMService()
        self.history: List[Dict[str, str]] = []
        
        self.director = Agent(
            name="Director",
            role="Creative Visionary",
            system_prompt="You are the Creative Director. You guide the visual style, pacing, and overall concept. Keep it concise.",
            llm_service=self.llm
        )
        self.script_writer = Agent(
            name="ScriptWriter",
            role="Content Creator",
            system_prompt="You are the ScriptWriter. You write engaging, fast-paced scripts for YouTube Shorts.",
            llm_service=self.llm
        )
        self.fact_checker = Agent(
            name="FactChecker",
            role="Quality Assurance",
            system_prompt="You are the FactChecker. You verify claims and ensure the script is accurate. Point out flaws.",
            llm_service=self.llm
        )
        self.video_prompter = Agent(
            name="VideoPrompter",
            role="Cinematographer",
            system_prompt="You are the Video Prompter. You convert script segments into detailed, cinematic AI video generation prompts.",
            llm_service=self.llm
        )
        
        self.agents = {
            "Director": self.director,
            "ScriptWriter": self.script_writer,
            "FactChecker": self.fact_checker,
            "VideoPrompter": self.video_prompter
        }

    def _optimize_history(self) -> str:
        """Token optimization: compress older history if it gets too long."""
        # Simple string representation for now
        compressed = ""
        for msg in self.history[-5:]: # Keep last 5 turns to save tokens
            compressed += f"[{msg['sender']}]: {msg['content']}\n"
        return compressed

    def run_workflow(self, topic: str, category: str, video_format: str = "DOCUMENTARY") -> Dict[str, Any]:
        """Runs the orchestrator loop to produce script and video prompts."""
        logger.info(f"Starting Multi-Agent Workflow for topic: {topic} (Format: {video_format})")
        
        # Inject specialized prompts based on video format
        if video_format == "VIRAL_PROMPT":
            self.script_writer.system_prompt = (
                "Act as a viral YouTube Shorts and TikTok creator specializing in the AI, design, and passive income niche. "
                "Your channel style relies on showing multi-layered, ultra-valuable prompts on screen, forcing viewers to pause, screenshot, and re-watch the video.\n\n"
                "Write a complete, ready-to-record vertical video script based on the topic/tools provided.\n\n"
                "### The Three Content Pillars of the Script:\n"
                "1. Image Generation: The video must feature a highly specific prompt for Midjourney, DALL-E, or Stable Diffusion that generates viral-quality visuals.\n"
                "2. High-Retention Text: The video must provide an automated text prompt structure (for scripts, hooks, or copy) that guarantees audience engagement.\n"
                "3. Monetization Engine: The video must seamlessly integrate a concrete monetization strategy explaining exactly how the viewer makes money with this setup.\n\n"
                "### Execution Blueprint\n"
                "1. The Frame-1 Hook (0:00 - 0:03): Start instantly with a high-stakes financial problem or a secret workflow.\n"
                "2. The Hype / Setup (0:03 - 0:10): Introduce the stack. Explain that combining a secret text model framework with a precise art generator creates an instant income stream.\n"
                "3. The Value Payload & Pause Cue (0:10 - 0:25): Show the multi-part master prompt clearly on screen. Call out its key variables. Instruct the viewer to pause and screenshot.\n"
                "4. The Proof / Financial Output (0:25 - 0:35): Describe the mind-blowing visual asset and text output it spits out, followed by a step-by-step breakdown of how to monetize it.\n"
                "5. The Psychological Loop: Do not say 'subscribe' or 'thanks for watching.' End the script mid-thought so it perfectly blends right back into the opening hook line.\n\n"
                "### Formatting Requirement\n"
                "Deliver the final script strictly as a two-column markdown table:\n"
                "| Visual & Text-on-Screen Cues | Audio |\n"
                "|---|---|\n"
            )
        elif video_format == "REDDIT_STORY":
            self.script_writer.system_prompt = (
                "Act as a viral Reddit Story YouTube Shorts creator. Your goal is to keep the viewer hooked to the very last second.\n\n"
                "Write a complete, ready-to-record vertical video script based on the topic provided.\n\n"
                "### Execution Blueprint\n"
                "1. The Frame-1 Hook (0:00 - 0:03): Start with an outrageous, highly relatable, or shocking personal statement (e.g., 'I (24F) ruined my wedding because...').\n"
                "2. The Escalation (0:03 - 0:20): Rapidly build the narrative. Introduce the conflict and make the stakes feel incredibly high.\n"
                "3. The Climax/Twist (0:20 - 0:35): Drop a major plot twist or satisfying resolution.\n"
                "4. The Outro (0:35 - 0:40): A one-sentence wrap-up or question to the audience to drive comments.\n\n"
                "### Formatting Requirement\n"
                "Deliver the final script strictly as a two-column markdown table:\n"
                "| Visual & Text-on-Screen Cues | Audio |\n"
                "|---|---|\n"
            )
        elif video_format == "TOP_3":
            self.script_writer.system_prompt = (
                "Act as a viral Top 3 Countdown YouTube Shorts creator. Your goal is to build suspense so the viewer stays for Number 1.\n\n"
                "Write a complete, ready-to-record vertical video script based on the topic provided.\n\n"
                "### Execution Blueprint\n"
                "1. The Frame-1 Hook (0:00 - 0:03): Ask a high-stakes question or make a bold claim about the Top 3 list.\n"
                "2. Number 3 (0:03 - 0:15): Introduce the third item. Make it fascinating but leave room for escalation.\n"
                "3. Number 2 (0:15 - 0:25): Introduce the second item. It must be significantly more shocking or intense than Number 3.\n"
                "4. Number 1 (0:25 - 0:35): The grand reveal. This must absolutely blow the viewer's mind and deliver on the promise of the hook.\n\n"
                "### Formatting Requirement\n"
                "Deliver the final script strictly as a two-column markdown table:\n"
                "| Visual & Text-on-Screen Cues | Audio |\n"
                "|---|---|\n"
            )
        elif video_format == "DID_YOU_KNOW":
            self.script_writer.system_prompt = (
                "Act as a viral 'Did You Know' educational YouTube Shorts creator. Your goal is to melt the viewer's brain with unbelievable facts.\n\n"
                "Write a complete, ready-to-record vertical video script based on the topic provided.\n\n"
                "### Execution Blueprint\n"
                "1. The Frame-1 Hook (0:00 - 0:03): Present an impossible paradox, a bizarre phenomenon, or a 'glitch in the matrix' fact.\n"
                "2. The Explanation (0:03 - 0:20): Explain the science or history behind the hook using extremely simple, vivid analogies.\n"
                "3. The Mind-Blowing Twist (0:20 - 0:35): Reveal a secondary fact that completely changes the context of the explanation.\n"
                "4. The Loop (0:35 - 0:40): End mid-sentence so it perfectly loops back into the opening hook.\n\n"
                "### Formatting Requirement\n"
                "Deliver the final script strictly as a two-column markdown table:\n"
                "| Visual & Text-on-Screen Cues | Audio |\n"
                "|---|---|\n"
            )
        
        # Turn 1: Director sets the vision
        vision_msg = f"We need a short about {topic} in the {category} category. What is the visual and narrative vision?"
        vision_reply = self.director.generate_reply(vision_msg)
        self.history.append({"sender": "Director", "content": vision_reply})
        
        # Turn 2: ScriptWriter drafts the script
        script_msg = f"Based on the Director's vision, draft a 30-second YouTube Short script.\nVision: {vision_reply}"
        script_reply = self.script_writer.generate_reply(script_msg, self._optimize_history())
        self.history.append({"sender": "ScriptWriter", "content": script_reply})
        
        # Turn 3: FactChecker reviews
        fact_msg = f"Review this script for factual accuracy. Only reply with corrections or say 'APPROVED'.\nScript: {script_reply}"
        fact_reply = self.fact_checker.generate_reply(fact_msg, self._optimize_history())
        self.history.append({"sender": "FactChecker", "content": fact_reply})
        
        # Turn 4: Video Prompter creates shot list
        shot_msg = f"The script is finalized. Generate 3-5 distinct, highly detailed prompts for an AI Video Generator (like Runway/Luma). Make them cinematic."
        shot_reply = self.video_prompter.generate_reply(shot_msg, self._optimize_history())
        self.history.append({"sender": "VideoPrompter", "content": shot_reply})
        
        # --- NEW PIPELINE INTEGRATION ---
        try:
            from backend.generation_engine.audio_models import AudioGenerationEngine
            from backend.generation_engine.video_models import VideoGenerationEngine
            from backend.pipeline.composer import VideoComposer
            import os

            audio_engine = AudioGenerationEngine()
            video_engine = VideoGenerationEngine()
            composer = VideoComposer()

            # 1. Generate Voiceover from Script
            logger.info("Starting Audio Generation...")
            audio_path = audio_engine.generate_voiceover(script_reply)

            # Calculate exact duration for each clip to match the audio perfectly
            from moviepy.editor import AudioFileClip
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            audio_clip.close()
            clip_duration = total_duration / 3.0

            # 2. Generate Video Clips (Mocked from the shot list)
            # In a real app, you would parse the shot_reply into a list of specific prompts.
            logger.info(f"Starting Video B-roll Generation (Each clip: {clip_duration:.2f}s)...")
            video_clips = [
                video_engine.generate_broll("Shot 1", duration=clip_duration),
                video_engine.generate_broll("Shot 2", duration=clip_duration),
                video_engine.generate_broll("Shot 3", duration=clip_duration)
            ]

            # 3. Assemble Final Video
            logger.info("Starting Final Video Assembly...")
            output_video = os.path.join(os.getcwd(), "tmp", f"final_video_{hash(script_reply)}.mp4")
            final_path = composer.assemble_final_video(video_clips, audio_path, output_video)
        except Exception as e:
            logger.error(f"Pipeline generation failed: {e}")
            final_path = None
            
        return {
            "vision": vision_reply,
            "script": script_reply,
            "fact_check": fact_reply,
            "video_prompts": shot_reply,
            "history": self.history,
            "final_video_path": final_path
        }
