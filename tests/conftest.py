"""
Global Pytest Fixtures for Autonomous Shorts System.
Mocks external network services (LLM, YouTube API, external scraping)
to guarantee zero rate-limit issues, lightning-fast test execution,
and 100% deterministic test passes.
"""

import json
import pytest
from backend.services.llm_service import LLMService, llm_service
from backend.services.youtube_service import YouTubeService, youtube_service


@pytest.fixture(autouse=True)
def mock_all_llm(monkeypatch):
    """
    Universal mock for LLMService.generate across all test modules.
    Intercepts LLM prompts and returns appropriate schema-compliant mocks.
    """
    def _mock_generate(self_or_prompt, *args, **kwargs):
        if isinstance(self_or_prompt, str):
            prompt = self_or_prompt
        elif args:
            prompt = args[0]
        else:
            prompt = kwargs.get("prompt", "")

        json_mode = kwargs.get("json_mode", False)
        if len(args) >= 3 and isinstance(args[2], bool):
            json_mode = args[2]

        lower = prompt.lower()

        # 1. Hook Lab Scoring
        if "evaluate the following video hook" in lower or "curiosity" in lower:
            if json_mode:
                return json.dumps({
                    "curiosity": 85,
                    "surprise": 80,
                    "emotional_impact": 75,
                    "clarity": 90,
                    "novelty": 80
                })

        # 2. Viewer Persona Evaluation
        if "evaluate this short script" in lower or "stopped_scrolling" in lower or "persona" in lower:
            if json_mode:
                return json.dumps({
                    "stopped_scrolling": True,
                    "retention_1s": 88,
                    "retention_3s": 82,
                    "retention_5s": 78,
                    "clarity_score": 90,
                    "curiosity_score": 85,
                    "payoff_score": 80,
                    "rewatch_potential": 75,
                    "critique": "Crisp premise and engaging pacing."
                })

        # 3. Production Statistics / Daily Review
        if "production statistics" in lower or "daily review" in lower:
            if json_mode:
                return json.dumps({
                    "what_worked": "High-retention hooks performed well.",
                    "what_failed": "Avoid overly dense jargon.",
                    "what_surprised": "Space category showed strong audience growth.",
                    "category_insights": "Maintain 80/20 portfolio split.",
                    "lessons": "Focus on 3-second hook clarity."
                })

        # 4. Comment Engine / Topic Extraction
        if "mariana trench" in lower and json_mode:
            return json.dumps({
                "is_idea": True,
                "derived_topic": "The Mariana Trench Part 2",
                "category": "science",
                "opportunity_score": 88.5
            })
        if "craters" in lower and json_mode:
            return json.dumps({
                "is_idea": True,
                "derived_topic": "Why Does The Moon Have So Many Craters?",
                "category": "space",
                "opportunity_score": 91.0
            })

        # 5. Fact Checking
        if "fact check" in lower or "claims" in lower:
            if json_mode:
                return json.dumps({
                    "status": "VERIFIED",
                    "confidence": 0.95,
                    "reasoning": "Scientific consensus confirmed.",
                    "repaired_narration": None
                })

        # Default fallback
        if json_mode:
            return json.dumps({
                "status": "ok",
                "is_idea": False,
                "score": 85
            })

        return "Deterministic test generation output"

    monkeypatch.setattr(LLMService, "generate", _mock_generate)
    monkeypatch.setattr(llm_service, "generate", _mock_generate)


@pytest.fixture(autouse=True)
def mock_youtube_auth(monkeypatch):
    """Ensure YouTube auth calls don't perform external network refresh."""
    monkeypatch.setattr(YouTubeService, "is_authenticated", lambda self: False)
    monkeypatch.setattr(youtube_service, "is_authenticated", lambda: False)
