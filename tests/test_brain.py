"""
Unit tests for Content Brain, Daily Review, Comment Engine, and Human Override filters.
"""

import json
import pytest
from backend.learning.content_brain import ContentBrain
from backend.learning.daily_review import DailyReviewAgent
from backend.learning.comment_engine import CommentEngine
from backend.services.llm_service import LLMService, llm_service


@pytest.fixture(autouse=True)
def mock_brain_llm(monkeypatch):
    """Mock LLM generation for brain and comment engine tests."""
    def _mock_generate(self_or_prompt, *args, **kwargs):
        # Support both class method and function signature
        if isinstance(self_or_prompt, str):
            prompt = self_or_prompt
        elif args:
            prompt = args[0]
        else:
            prompt = kwargs.get("prompt", "")
        
        json_mode = kwargs.get("json_mode", False)
        if len(args) >= 3 and isinstance(args[2], bool):
            json_mode = args[2]

        lower_p = prompt.lower()
        if "mariana trench" in lower_p and json_mode:
            return json.dumps({
                "is_idea": True,
                "derived_topic": "The Mariana Trench Part 2",
                "category": "science",
                "opportunity_score": 88.5
            })
        if "craters" in lower_p and json_mode:
            return json.dumps({
                "is_idea": True,
                "derived_topic": "Why Does The Moon Have So Many Craters?",
                "category": "space",
                "opportunity_score": 91.0
            })
        if "production statistics" in lower_p and json_mode:
            return json.dumps({
                "what_worked": "High-retention hooks performed well.",
                "what_failed": "Avoid overly dense jargon.",
                "what_surprised": "Space category showed strong audience growth.",
                "category_insights": "Maintain 80/20 portfolio split.",
                "lessons": "Focus on 3-second hook clarity."
            })
        if json_mode:
            return json.dumps({"is_idea": False})
        return "Deterministic test reply"

    monkeypatch.setattr(LLMService, "generate", _mock_generate)
    monkeypatch.setattr(llm_service, "generate", _mock_generate)


def test_content_brain_status_and_leaderboard():
    brain = ContentBrain()
    status = brain.get_status()
    assert "total_categories" in status
    assert status["total_categories"] >= 15
    assert "characters" in status
    assert len(status["characters"]) >= 2
    assert "dynamic_portfolio_mix" in status
    assert isinstance(status["dynamic_portfolio_mix"], dict)

    leaderboard = brain.get_category_leaderboard()
    assert len(leaderboard) > 0
    assert "category" in leaderboard[0]
    assert "score" in leaderboard[0]


def test_character_roster_and_tracking():
    brain = ContentBrain()
    chars = brain.get_all_characters()
    names = [c["name"] for c in chars]
    assert "Byte" in names
    assert "Sam" in names

    # Increment usage
    brain.register_character_appearance("Byte")
    updated = brain.get_all_characters()
    byte_char = next(c for c in updated if c["name"] == "Byte")
    assert byte_char["appearances"] >= 1


def test_human_override_blacklists():
    brain = ContentBrain()
    
    # Add blacklist
    test_word = "banned_crypto_coin"
    brain.add_override_blacklist("keyword", test_word, reason="Spam filter")

    # Verify blocked
    blocked, reason = brain.check_blacklist(f"How to buy {test_word} quickly", "finance")
    assert blocked is True
    assert reason is not None

    # Safe topic should pass
    clean_blocked, _ = brain.check_blacklist("Why stars twinkle in the night sky", "science")
    assert clean_blocked is False


def test_daily_review_cycle():
    agent = DailyReviewAgent()
    result = agent.run_review(target_date="2026-09-11")
    assert result.review_date == "2026-09-11"
    assert len(result.what_worked) > 0
    assert len(result.lessons) > 0
    assert len(result.strategy_changes) > 0
    assert isinstance(result.weight_adjustments, dict)


def test_comment_to_content_pipeline():
    engine = CommentEngine()
    incoming = [
        {"author": "Viewer99", "text": "Can you do part 2 on the Mariana Trench?"},
        {"author": "SpaceFan", "text": "Why does the moon have so many craters?"},
        {"author": "SpamBot", "text": "hi"},  # Should be skipped
    ]
    candidates = engine.process_incoming_comments(incoming)
    assert len(candidates) == 2
    
    topics = [c.derived_topic for c in candidates]
    assert any("Mariana Trench" in t or "Part 2" in t for t in topics)
    assert any("Moon" in t or "Crater" in t for t in topics)
    for c in candidates:
        assert c.status == "PENDING"
        assert c.opportunity_score > 70


def test_active_editorial_guidelines():
    brain = ContentBrain()
    guidelines = brain.get_active_editorial_guidelines()
    assert isinstance(guidelines, str)
    assert len(guidelines) > 10
