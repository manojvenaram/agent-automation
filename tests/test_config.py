"""Unit tests for configuration loading and defaults."""
import os
from backend.core.config import AppConfig, load_config, settings


def test_default_config():
    cfg = AppConfig()
    assert cfg.video_width == 1080
    assert cfg.video_height == 1920
    assert cfg.video_fps == 30
    assert cfg.target_words_per_minute == 145
    assert cfg.fact_confidence_threshold == 0.80
    assert cfg.minimum_quality_score == 75
    assert cfg.auto_publish is False


def test_env_override():
    os.environ["VIDEO_WIDTH"] = "1080"
    os.environ["VIDEO_HEIGHT"] = "1920"
    os.environ["TARGET_WORDS_PER_MINUTE"] = "150"
    cfg = load_config()
    assert cfg.video_width == 1080
    assert cfg.target_words_per_minute == 150
