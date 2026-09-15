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
        """Generate YouTube Shorts metadata package with real-time SEO competitor analysis."""
        logger.info(f"Generating YouTube metadata for '{topic}'...")
        metadata_dir = project_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        sources_summary = ", ".join([s.title for s in sources[:3]])

        # 1. Competitor Analysis via DDGS
        competitor_titles = []
        try:
            from duckduckgo_search import DDGS
            logger.info("Scraping top ranking YouTube Shorts competitors for SEO analysis...")
            results = DDGS().text(f"site:youtube.com {topic} #shorts", max_results=5)
            competitor_titles = [r.get("title", "") for r in results if r.get("title")]
        except Exception as e:
            logger.warning(f"Competitor analysis failed: {e}")

        prompt = (
            f"Topic: {topic}\n"
            f"Script:\n{script.full_narration}\n"
            f"Sources: {sources_summary}\n\n"
            f"Current Top Ranking Competitor Titles on YouTube:\n{json.dumps(competitor_titles)}\n\n"
            f"Task: Generate a highly viral YouTube Shorts SEO metadata package.\n"
            f"Requirements:\n"
            f"1. Generate 5 curiosity-driven titles under 80 characters. Analyze the competitor titles to create something even more clickable.\n"
            f"2. Pick the single strongest high-CTR title.\n"
            f"3. Write an engaging 2-3 paragraph description packed with proven search terms.\n"
            f"4. Pick 5-7 focused hashtags combining broad tags (like #Shorts, #viral) and highly specific niche tags.\n"
            f"5. Provide 6-10 SEO search tags to rank in the YouTube algorithm.\n"
            f"6. Generate a highly controversial or engaging pinned comment question to farm comments and boost engagement.\n"
            f"Output strictly JSON:\n"
            f'{{"titles": ["..."], "selected_title": "...", "description": "...", "hashtags": ["#Shorts", "..."], "tags": ["..."], "pinned_comment": "..."}}'
        )

        response = llm_service.generate(prompt, json_mode=True)
        data = None
        try:
            # Clean markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            data = json.loads(clean_response.strip())
        except Exception as e:
            logger.warning(f"Metadata JSON parsing failed: {e}. Using dynamic fallback.")

        if not data or not data.get("titles"):
            fallback_title = f"The Truth About {topic.title()}"
            data = {
                "titles": [
                    fallback_title,
                    f"What You Didn't Know About {topic.title()}",
                ],
                "selected_title": f"{fallback_title} #Shorts",
                "description": (
                    f"{script.hook}\n\n"
                    f"Learn more about {topic} in this quick #Shorts video!\n\n"
                    f"Sources:\n"
                    + "\n".join([f"- {s.title}: {s.url}" for s in sources])
                    + "\n\n#Shorts #Facts #Trending"
                ),
                "hashtags": ["#Shorts", "#Facts", "#Trending"],
                "tags": [topic.lower(), "facts", "shorts", "trending"],
                "pinned_comment": f"What are your thoughts on {topic}? Tell us in the comments! 👇",
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
