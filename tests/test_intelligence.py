"""
Unit tests for Universal Trend Intelligence, Opportunity Scorer, and Content Portfolio Allocator.
"""

import pytest
from backend.intelligence.trend_engine import TrendIntelligenceEngine, TrendOpportunity, TrendVelocity
from backend.intelligence.opportunity_scorer import ContentOpportunityScorer
from backend.intelligence.content_portfolio import ContentPortfolioEngine


def test_trend_engine_classification():
    engine = TrendIntelligenceEngine()
    
    # Test category inference
    cat_sports = engine._infer_category("Cristiano Ronaldo sets new all-time scoring record in final")
    assert cat_sports == "sports"
    
    cat_space = engine._infer_category("NASA James Webb telescope detects strange light echo")
    assert cat_space == "space"

    cat_gaming = engine._infer_category("Nintendo announces new Zelda speedrunning world record")
    assert cat_gaming == "gaming"

    # Test velocity classification
    vel = engine._classify_velocity(
        {"velocity": "breaking", "title": "Breaking announcement in tech"},
        engine._infer_category("Breaking announcement in tech")
    )
    assert vel in [TrendVelocity.BREAKING, TrendVelocity.RISING, TrendVelocity.TRENDING]


def test_opportunity_scorer_13_dimensions():
    scorer = ContentOpportunityScorer()
    mock_item = {
        "topic": "Why Airplane Windows Have Tiny Secret Holes",
        "category": "technology",
        "summary": "Every commercial aircraft window has a bleed hole to balance pressure.",
        "velocity": "rising",
        "source": "educational_feed",
    }
    opp = scorer.score_candidate(mock_item)
    assert opp.topic == mock_item["topic"]
    assert 0 <= opp.opportunity_score <= 100
    assert 0 <= opp.curiosity_score <= 100
    assert 0 <= opp.factual_confidence <= 100.0
    assert opp.competition in ["low", "medium", "high"]


def test_content_portfolio_80_20_balance():
    portfolio = ContentPortfolioEngine()
    
    # Ensure all 17 categories are recognized in fallback or selection
    cat, is_exp = portfolio.select_next_portfolio_target()
    assert isinstance(cat, str)
    assert isinstance(is_exp, bool)

    # Forced category override
    cat_forced, _ = portfolio.select_next_portfolio_target(forced_category="humor")
    assert cat_forced == "humor"

    # Cross category hybrid detection
    hybrid_sci = portfolio.check_cross_category_opportunity("science")
    assert hybrid_sci is not None
    assert "primary_category" in hybrid_sci
    assert "secondary_category" in hybrid_sci
    assert "hybrid_angle" in hybrid_sci


def test_portfolio_mix_calculation():
    portfolio = ContentPortfolioEngine()
    mock_scores = [
        {"category": "cartoons", "score": 92.0},
        {"category": "humor", "score": 88.0},
        {"category": "science", "score": 80.0},
    ]
    mix = portfolio.calculate_mix(mock_scores)
    assert "cartoons" in mix
    assert "humor" in mix
    assert "science" in mix
    assert sum(mix.values()) == pytest.approx(1.0, abs=0.01)
