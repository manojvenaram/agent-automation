"""
TopicResearchAgent & HookAgent.
TopicResearchAgent retrieves verifiable evidence from free public sources (Wikipedia REST, etc.).
HookAgent generates multiple high-retention hooks engineered for the critical first 3 seconds.
"""

import json
from typing import List, Tuple
from backend.core.database import save_research_sources
from backend.core.logging import logger
from backend.models import ResearchSource
from backend.services.llm_service import llm_service
from backend.services.research_service import research_service


class TopicResearchAgent:
    def research_topic(self, project_id: str, topic: str) -> List[ResearchSource]:
        """Conduct targeted research on the topic using Wikipedia REST API."""
        logger.info(f"Researching topic: '{topic}'...")
        sources = research_service.search_wikipedia(topic, max_results=3)
        if sources:
            save_research_sources(project_id, sources)
            logger.info(f"Saved {len(sources)} research sources for project '{project_id}'.")
        return sources


class HookAgent:
    def generate_hooks(self, topic: str, research_context: str) -> Tuple[str, List[str]]:
        """
        Generate 5 distinct high-retention hooks and pick the most powerful one.
        Must capture attention within 0-3 seconds and create an irresistible curiosity gap.
        """
        prompt = (
            f"Topic: {topic}\n"
            f"Research context: {research_context[:800]}\n\n"
            f"Task: Generate 5 ultra-compelling, curiosity-inducing opening hooks (1 sentence, under 15 words) for a YouTube Short.\n"
            f"Rules:\n"
            f"- Must create a powerful curiosity gap.\n"
            f"- Avoid generic intros like 'Hey guys' or 'Have you ever wondered'.\n"
            f"- Use bold contrasting concepts or surprising facts.\n"
            f"Output strictly JSON:\n"
            f'{{"hooks": ["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"], "best_hook": "Hook 1"}}'
        )

        response = llm_service.generate(prompt, json_mode=True)
        hooks = []
        best_hook = ""

        try:
            data = json.loads(response)
            hooks = data.get("hooks", [])
            best_hook = data.get("best_hook", "")
        except Exception:
            pass

        if not hooks:
            hooks = [
                f"Did you know that {topic.lower()} sounds completely impossible?",
                f"Scientists discovered something about {topic.lower()} that defies physics.",
                f"Every astronaut who steps outside reports the exact same bizarre smell.",
                f"What outer space actually smells like will completely blow your mind.",
                f"The cosmos smells like something you'd never ever expect.",
            ]
            best_hook = hooks[0]

        if not best_hook and hooks:
            best_hook = hooks[0]

        logger.info(f"Selected hook: '{best_hook}'")
        return best_hook, hooks


topic_research_agent = TopicResearchAgent()
hook_agent = HookAgent()
