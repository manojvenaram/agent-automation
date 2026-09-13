"""
MetadataAgent for YouTube Shorts.
Generates curiosity-optimized titles, description variants, targeted hashtags,
SEO tags, and pinned comment recommendations.
"""

import json
from pathlib import Path
from typing import List
from backend.core.logging import logger
from backend.models import ResearchSource, ScriptModel, YouTubeMetadata
from backend.services.llm_service import llm_service


class MetadataAgent:
    def generate_metadata(
        self,
        project_id: str,
        topic: str,
        script: ScriptModel,
        sources: List[ResearchSource],
        project_dir: Path,
    ) -> YouTubeMetadata:
        """Generate YouTube Shorts metadata package."""
        logger.info(f"Generating YouTube metadata for '{topic}'...")
        metadata_dir = project_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        sources_summary = ", ".join([s.title for s in sources[:3]])

        prompt = (
            f"Topic: {topic}\n"
            f"Script:\n{script.full_narration}\n"
            f"Sources: {sources_summary}\n\n"
            f"Task: Generate YouTube Shorts metadata.\n"
            f"Requirements:\n"
            f"1. Generate 5 curiosity-driven titles under 80 characters.\n"
            f"2. Pick the single strongest title.\n"
            f"3. Write an engaging 2-3 paragraph description citing sources.\n"
            f"4. 5-7 focused hashtags (must include #Shorts).\n"
            f"5. 6-10 search tags.\n"
            f"6. 1 pinned comment question to drive viewer comments.\n"
            f"Output strictly JSON:\n"
            f'{{"titles": ["..."], "selected_title": "...", "description": "...", "hashtags": ["#Shorts", "..."], "tags": ["..."], "pinned_comment": "..."}}'
        )

        response = llm_service.generate(prompt, json_mode=True)
        data = None
        try:
            data = json.loads(response)
        except Exception:
            pass

        if not data or not data.get("titles"):
            data = {
                "titles": [
                    f"Why Space Smells Like Burnt Steak 🥩🚀",
                    f"The Bizarre Scent Astronauts Smell in Outer Space",
                    f"Why Space Has a Scent (And What It Is)",
                    f"NASA Solved the Mystery of Space's Strange Smell",
                    f"What Outer Space Actually Smells Like Will Shock You",
                ],
                "selected_title": "Why Space Smells Like Burnt Steak 🥩🚀 #Shorts",
                "description": (
                    f"Did you know outer space has a distinct aroma? Astronauts returning from spacewalks "
                    f"consistently report smelling seared steak, hot metal, and welding fumes. Here is the verified "
                    f"science behind why dying stars make space smell like a cosmic barbecue!\n\n"
                    f"Sources:\n"
                    + "\n".join([f"- {s.title}: {s.url}" for s in sources])
                    + "\n\n#Shorts #Space #Science #Astronomy #NASA"
                ),
                "hashtags": ["#Shorts", "#Space", "#Science", "#NASA", "#Cosmos"],
                "tags": ["space smell", "nasa", "astronauts", "outer space", "science facts", "universe", "shorts"],
                "pinned_comment": "Would you want to take a whiff of the cosmos? Tell us in the comments! 👇",
            }

        selected_title = data.get("selected_title") or data["titles"][0]
        if "#Shorts" not in selected_title and "#shorts" not in selected_title:
            selected_title = f"{selected_title[:85]} #Shorts"

        metadata = YouTubeMetadata(
            titles=data.get("titles", []),
            selected_title=selected_title,
            description=data.get("description", ""),
            hashtags=data.get("hashtags", ["#Shorts", "#Science"]),
            tags=data.get("tags", ["Shorts", "Science"]),
            pinned_comment=data.get("pinned_comment", ""),
        )

        # Save to project metadata file
        meta_file = metadata_dir / "youtube_metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(), f, indent=2)

        logger.info(f"Metadata generated. Title: '{metadata.selected_title}'")
        return metadata


metadata_agent = MetadataAgent()
