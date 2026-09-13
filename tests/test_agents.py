"""Unit tests for specialized agent logic."""
import json
import uuid
import pytest
from backend.agents.trend_scout import TrendScoutAgent, TopicEvaluatorAgent
from backend.agents.researcher import HookAgent
from backend.agents.script_writer import ScriptWriterAgent
from backend.agents.fact_checker import FactCheckerAgent
from backend.agents.quality_control import QualityControlAgent
from backend.services.ollama_service import ollama_service
from backend.models import (
    ResearchSource,
    ScriptModel,
    ScriptScene,
    FactCheckReport,
    FactualClaim,
    ClaimStatus,
)


@pytest.fixture(autouse=True)
def mock_ollama_for_unit_tests(monkeypatch):
    """Mock external LLM calls to execute unit tests fast and deterministically."""
    def _mock_generate(prompt, system_prompt=None, json_mode=False, temperature=None, timeout=None):
        lower_p = prompt.lower()
        if "hook" in lower_p and json_mode:
            return json.dumps({
                "hooks": [
                    "Why does space smell like seared steak?",
                    "What astronauts smell in space will shock you.",
                    "Space smells like a cosmic barbecue.",
                ],
                "best_hook": "Why does space smell like seared steak?",
            })
        if "script" in lower_p and json_mode:
            return json.dumps({
                "hook": "Why does space smell like seared steak?",
                "context": "Astronauts notice a distinct aroma after spacewalks.",
                "main_facts": "High energy polycyclic aromatic hydrocarbons float through the universe from dying stars.",
                "payoff": "When airlocks repressurize, they smell like a celestial barbecue.",
                "cta": "Subscribe for more cosmic secrets!",
                "scenes": [
                    {"scene_index": 1, "narration": "Why does space smell like seared steak?", "duration_est": 4.0, "visual_description": "Astronaut floating in space"},
                    {"scene_index": 2, "narration": "Astronauts notice a distinct aroma after spacewalks.", "duration_est": 5.0, "visual_description": "Airlock module"},
                    {"scene_index": 3, "narration": "High energy polycyclic aromatic hydrocarbons float through space.", "duration_est": 8.0, "visual_description": "Supernova nebula"},
                    {"scene_index": 4, "narration": "When airlocks repressurize, they smell like barbecue.", "duration_est": 6.0, "visual_description": "Cosmic particles"},
                    {"scene_index": 5, "narration": "Subscribe for more cosmic secrets!", "duration_est": 3.0, "visual_description": "Galaxy rotation"},
                ],
            })
        if "claim" in lower_p and json_mode:
            return json.dumps({
                "claims": [
                    {"claim_text": "Space has an aroma after spacewalks", "status": "VERIFIED", "confidence": 0.98, "evidence": "Documented by NASA astronaut debriefs."},
                    {"claim_text": "Polycyclic aromatic hydrocarbons float through space", "status": "VERIFIED", "confidence": 0.95, "evidence": "Confirmed by space spectroscopy."},
                ],
                "overall_confidence": 0.96,
            })
        return "Unit test fallback response"

    monkeypatch.setattr(ollama_service, "generate", _mock_generate)


def test_topic_evaluator_scoring():
    evaluator = TopicEvaluatorAgent()
    candidates = [
        {"topic": "Why Does Space Smell Like Something Burning", "category": "space", "premise": "Astronauts detect steak odor.", "hook_idea": "Did you know space has an aroma?"},
        {"topic": "A Normal Rock on the Ground", "category": "nature", "premise": "Just ordinary rocks.", "hook_idea": "Here is a rock."},
    ]
    winner = evaluator.evaluate_and_select_topic(candidates)
    assert winner["topic"] == "Why Does Space Smell Like Something Burning"
    assert winner["composite_score"] > 0.70


def test_hook_agent_generation():
    hook_ag = HookAgent()
    best_hook, hooks = hook_ag.generate_hooks(
        topic="Why Space Smells Like Something Burning",
        research_context="Astronauts describe an aroma of seared steak after EVAs."
    )
    assert len(hooks) >= 1
    assert len(best_hook) > 10


def test_script_writer_duration_and_scenes():
    writer = ScriptWriterAgent()
    pid = f"test_sw_{uuid.uuid4().hex[:6]}"
    sources = [
        ResearchSource(url="https://en.wikipedia.org/wiki/Space_smell", title="Space Smell", extract="Interstellar hydrocarbons create burnt steak smell.")
    ]
    script = writer.generate_script(
        project_id=pid,
        topic="Why Space Smells Like Something Burning",
        sources=sources,
        hook="Why does space smell like seared steak?",
    )
    assert script.word_count > 20
    assert script.estimated_duration_sec > 10.0
    assert len(script.scenes) >= 3


def test_fact_checker_evaluation():
    checker = FactCheckerAgent()
    pid = f"test_fc_{uuid.uuid4().hex[:6]}"
    sources = [
        ResearchSource(url="https://en.wikipedia.org/wiki/Space_smell", title="Space Smell", extract="Interstellar hydrocarbons create burnt steak smell.")
    ]
    script = ScriptModel(
        hook="Why does space smell like seared steak?",
        context="Astronauts notice it after spacewalks.",
        main_facts="High energy polycyclic aromatic hydrocarbons float through space.",
        payoff="It literally smells like cosmic barbecue.",
        cta="Subscribe for more!",
        full_narration="Why does space smell like seared steak? High energy polycyclic aromatic hydrocarbons float through space.",
        word_count=18,
        estimated_duration_sec=7.5,
        scenes=[],
    )
    report = checker.verify_script(pid, script, sources)
    assert isinstance(report, FactCheckReport)
    assert report.overall_confidence >= 0.80
    assert report.passed is True


def test_quality_control_diagnostics():
    qc_agent = QualityControlAgent()
    script = ScriptModel(
        hook="Why does space smell like burnt steak?",
        context="Astronauts notice it.",
        main_facts="Hydrocarbons from dying stars react with oxygen.",
        payoff="Cosmic barbecue.",
        cta="",
        full_narration="Why does space smell like burnt steak? Hydrocarbons from dying stars react with oxygen.",
        word_count=14,
        estimated_duration_sec=6.0,
        scenes=[],
    )
    fact_report = FactCheckReport(overall_confidence=0.92, claims=[], passed=True)
    
    # Missing video file should fail technical QC
    report = qc_agent.evaluate_video(
        project_id="missing_proj",
        video_path="nonexistent_video.mp4",
        script=script,
        fact_report=fact_report,
        subtitles_path="nonexistent.ass",
    )
    assert report.passed is False
    action, reason = qc_agent.diagnose_repair_action(report)
    assert action in ["RERENDER_VIDEO", "REWRITE_SCRIPT", "REGENERATE_VOICE"]
