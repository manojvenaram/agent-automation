"""
Unit tests for Creative Director, Story Engine, Hook Lab, Viewer Simulator, and Cartoon Engine.
"""

from pathlib import Path
from PIL import Image
import pytest
from backend.creative.creative_director import CreativeDirectorAgent, ShortsFormat, VisualTreatment
from backend.creative.story_engine import StoryEngine, StoryStructure
from backend.creative.hook_lab import HookLab
from backend.creative.viewer_simulator import ViewerSimulatorAgent, ViewerPersona
from backend.creative.cartoon_engine import CartoonEngine, CharacterPose


def test_creative_director_format_and_humor():
    director = CreativeDirectorAgent()

    # High humor for comedy
    h_comedy = director.calculate_humor_suitability("The Funniest Mistake in Football History", "sports")
    assert h_comedy >= 60

    # Zero humor guardrail for tragedy
    h_serious = director.calculate_humor_suitability("Major Earthquake Disaster and Casualties", "news")
    assert h_serious <= 10

    # Format selection
    fmt_cartoon = director.select_format("Byte tries cooking", "cartoon", humor_suitability=90)
    assert fmt_cartoon == ShortsFormat.MINI_CARTOON

    fmt_countdown = director.select_format("Top 3 Strangest Animals on Earth", "animals", humor_suitability=50)
    assert fmt_countdown == ShortsFormat.TOP_3

    fmt_mystery = director.select_format("The Unsolved Mystery of the Lost Ship", "mystery", humor_suitability=20)
    assert fmt_mystery == ShortsFormat.MYSTERY

    # Complete Creative Direction
    dir_result = director.determine_direction("Why Space Smells Weird", "space")
    assert dir_result.format in ShortsFormat
    assert dir_result.visual_treatment in VisualTreatment
    assert 0 <= dir_result.humor_suitability <= 100


def test_story_engine_structures():
    engine = StoryEngine()
    hook = "Nobody knew why this happened until yesterday."
    topic = "The Secret Chemistry of Ice Cream"

    for struct in StoryStructure:
        script = engine._generate_fallback_script(topic, "science", hook, struct, character_name="Byte")
        assert len(script.beats) >= 4
        assert script.total_words > 30
        assert script.estimated_duration_sec > 10.0
        assert hook in script.beats[0].narration


def test_hook_lab_10_candidates():
    lab = HookLab()
    hooks = lab.generate_hooks(
        topic="Why the Bermuda Triangle is Actually Solved",
        category="mystery",
        key_facts="Methane hydrate bubbles and rogue waves explain the missing ships.",
    )
    assert len(hooks) >= 10
    # Winner has highest composite score
    assert hooks[0].composite_score >= hooks[-1].composite_score
    for h in hooks:
        assert 0 <= h.composite_score <= 100
        assert 0 <= h.curiosity <= 100
        assert 0 <= h.retention_potential <= 100


def test_viewer_simulator_personas():
    sim = ViewerSimulatorAgent()
    hook = "Stop eating this food before you make this massive mistake."
    result = sim.simulate("Toxic Food Combinations", "food", hook)

    assert len(result.evaluations) == 7
    assert 0.0 <= result.scroll_stop_rate <= 1.0
    assert 0.0 <= result.composite_retention <= 100.0
    assert result.verdict in ["PASS", "REWRITE_HOOK"]

    # Verify all 7 personas evaluated
    personas_evaluated = {e.persona for e in result.evaluations}
    assert ViewerPersona.CASUAL_US in personas_evaluated
    assert ViewerPersona.GEN_Z in personas_evaluated
    assert ViewerPersona.TECH_ENTHUSIAST in personas_evaluated


def test_cartoon_engine_procedural_rendering(tmp_path):
    engine = CartoonEngine()
    
    # Test Byte character scene
    byte_output = tmp_path / "byte_test.jpg"
    engine.render_scene(
        character_name="Byte",
        pose=CharacterPose.CONFIDENT,
        caption_title="ROBOT LOGIC",
        dialogue="Human calculations are exactly 99.8% inefficient!",
        output_path=byte_output,
        theme="cyber",
    )
    assert byte_output.exists()
    with Image.open(byte_output) as img:
        assert img.size == (1080, 1920)

    # Test Sam character scene
    sam_output = tmp_path / "sam_test.jpg"
    engine.render_scene(
        character_name="Sam",
        pose=CharacterPose.SKEPTICAL,
        caption_title="SKEPTICAL HUMAN",
        dialogue="Wait a second... did you check the battery?",
        output_path=sam_output,
        theme="comedy",
    )
    assert sam_output.exists()
    with Image.open(sam_output) as img:
        assert img.size == (1080, 1920)

    # Test Duo side-by-side comedy scene
    duo_output = tmp_path / "duo_test.jpg"
    engine.render_duo_scene(
        pose_byte=CharacterPose.MALFUNCTION,
        pose_sam=CharacterPose.CONFIDENT,
        dialogue="I told you not to push that button!",
        speaking_char="Sam",
        output_path=duo_output,
    )
    assert duo_output.exists()
    with Image.open(duo_output) as img:
        assert img.size == (1080, 1920)
