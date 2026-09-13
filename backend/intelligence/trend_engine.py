"""
Universal Trend Intelligence Engine.
Continuously scans public internet feeds for emerging stories, breaking news,
viral moments, sports events, scientific discoveries, and seasonal opportunities.
Zero paid APIs.
"""

import datetime
import random
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import httpx
from backend.core.config import settings
from backend.core.database import is_blacklisted, get_recent_topics
from backend.core.logging import logger


class TrendVelocity(str, Enum):
    BREAKING = "BREAKING"
    RISING = "RISING"
    VIRAL = "VIRAL"
    TRENDING = "TRENDING"
    SEASONAL = "SEASONAL"
    EVERGREEN = "EVERGREEN"
    EMERGING = "EMERGING"
    NICHE = "NICHE"
    DECLINING = "DECLINING"


@dataclass
class TrendOpportunity:
    topic: str
    category: str
    premise: str
    velocity: TrendVelocity
    trend_type: str
    source_signal: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "category": self.category,
            "premise": self.premise,
            "velocity": self.velocity.value,
            "trend_type": self.trend_type,
            "source_signal": self.source_signal,
        }


class UniversalTrendEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "UniversalShortsAgent/2.0 (Public Research Bot; Contact: support@localagent.ai)"
        }

    def _classify_velocity(self, item: Dict[str, Any], category: str) -> TrendVelocity:
        """Classify velocity into the 9 trend velocity dimensions."""
        vel_str = str(item.get("velocity", "")).upper()
        if "BREAKING" in vel_str:
            return TrendVelocity.BREAKING
        if "RISING" in vel_str or "HIGH" in vel_str:
            return TrendVelocity.RISING
        if "VIRAL" in vel_str:
            return TrendVelocity.VIRAL
        if "SEASONAL" in vel_str:
            return TrendVelocity.SEASONAL
        return TrendVelocity.TRENDING

    def discover_trending_topics(self, category: Optional[str] = None, count: int = 15) -> List[Dict[str, Any]]:
        """Convenience method matching agent orchestrator interface with optional category filter."""
        items = self.gather_daily_intelligence(max_candidates=count * 2)
        if category and category.lower() != "autonomous":
            cat_lower = category.lower()
            matching = [it for it in items if it.get("category", "").lower() == cat_lower]
            if matching:
                return matching[:count]
        return items[:count]

    def gather_daily_intelligence(self, max_candidates: int = 15) -> List[Dict[str, Any]]:
        """
        Gathers trend signals from multiple independent public feeds and returns classified candidates.
        """
        logger.info("Universal Trend Engine: Gathering real-time internet intelligence across categories...")
        candidates: List[Dict[str, Any]] = []

        # 1. Google Trends Daily RSS
        gt_items = self._fetch_google_trends()
        candidates.extend(gt_items)

        # 2. Wikipedia Current Events & Trends
        wiki_items = self._fetch_wikipedia_trends()
        candidates.extend(wiki_items)

        # 3. HackerNews Tech & Innovation Signals
        hn_items = self._fetch_hackernews_signals()
        candidates.extend(hn_items)

        # 4. Seasonal & Historical Milestones
        calendar_items = self._get_calendar_milestones()
        candidates.extend(calendar_items)

        # Filter duplicates and human blacklists
        recent_topics = get_recent_topics(limit=100)
        filtered = []
        seen = set()

        for c in candidates:
            t = c["topic"].strip()
            lower_t = t.lower()
            if lower_t in seen:
                continue
            if is_blacklisted(t, category=c.get("category")):
                continue
            if any(past.lower() in lower_t or lower_t in past.lower() for past in recent_topics[:20]):
                continue
            seen.add(lower_t)
            filtered.append(c)

        # If external feeds were limited or offline, supplement with universal evergreen bank
        if len(filtered) < max_candidates:
            fallbacks = self._get_universal_fallback_bank()
            for fb in fallbacks:
                if fb["topic"].lower() not in seen and not is_blacklisted(fb["topic"], category=fb["category"]):
                    filtered.append(fb)
                    seen.add(fb["topic"].lower())

        random.shuffle(filtered)
        results = filtered[:max_candidates]
        logger.info(f"Universal Trend Engine: Discovered {len(results)} high-potential candidates across {len(set(r['category'] for r in results))} categories.")
        return results

    def _fetch_google_trends(self) -> List[Dict[str, Any]]:
        """Fetch daily search trends from Google Trends RSS."""
        trends = []
        try:
            url = "https://trends.google.com/trending/rss?geo=US"
            with httpx.Client(headers=self.headers, timeout=6.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    for item in root.findall("./channel/item")[:8]:
                        title = item.findtext("title", "").strip()
                        traffic = item.findtext("{https://trends.google.com/trending/rss}approx_traffic", "100K+")
                        desc = item.findtext("description", "")
                        if title:
                            category = self._infer_category(title + " " + desc)
                            trends.append({
                                "topic": title,
                                "category": category,
                                "premise": desc or f"Trending search surge: {traffic} queries in the United States.",
                                "trend_type": "VIRAL" if "M+" in traffic else "RISING",
                                "velocity": "HIGH",
                                "source_signal": "Google Trends",
                            })
        except Exception as e:
            logger.debug(f"Google Trends RSS skipped ({e})")
        return trends

    def _fetch_wikipedia_trends(self) -> List[Dict[str, Any]]:
        """Fetch notable historical and scientific events from Wikipedia."""
        events = []
        try:
            today = datetime.datetime.now(datetime.UTC)
            # Fetch on this day in history
            month, day = today.strftime("%B"), today.strftime("%d")
            url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{today.month}/{today.day}"
            with httpx.Client(headers=self.headers, timeout=6.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    for ev in data.get("selected", [])[:5]:
                        year = ev.get("year", "")
                        text = ev.get("text", "")
                        title = f"What Happened in {year}: {text[:60]}..."
                        events.append({
                            "topic": title,
                            "category": "history",
                            "premise": text,
                            "trend_type": "SEASONAL",
                            "velocity": "STEADY",
                            "source_signal": f"Wikipedia OnThisDay ({year})",
                        })
        except Exception as e:
            logger.debug(f"Wikipedia trends skipped ({e})")
        return events

    def _fetch_hackernews_signals(self) -> List[Dict[str, Any]]:
        """Fetch top breakthrough technology stories from HackerNews API."""
        signals = []
        try:
            with httpx.Client(headers=self.headers, timeout=5.0) as client:
                res = client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                if res.status_code == 200:
                    story_ids = res.json()[:6]
                    for sid in story_ids:
                        story_res = client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                        if story_res.status_code == 200:
                            s = story_res.json()
                            title = s.get("title", "")
                            if title and len(title) > 15:
                                signals.append({
                                    "topic": title,
                                    "category": "technology",
                                    "premise": f"Top innovation story discussed with {s.get('score', 100)}+ points.",
                                    "trend_type": "EMERGING",
                                    "velocity": "RISING",
                                    "source_signal": "HackerNews",
                                })
        except Exception as e:
            logger.debug(f"HackerNews signals skipped ({e})")
        return signals

    def _get_calendar_milestones(self) -> List[Dict[str, Any]]:
        """Calendar and seasonal milestones."""
        today = datetime.datetime.now(datetime.UTC)
        day_of_week = today.strftime("%A")
        month_name = today.strftime("%B")
        return [
            {
                "topic": f"Why Weekend Sleep In Never Actually Fixes Exhaustion",
                "category": "science",
                "premise": "Circadian rhythm biology reveals social jetlag actually worsens sleep debt.",
                "trend_type": "EVERGREEN",
                "velocity": "STEADY",
                "source_signal": "Calendar Psychology",
            },
            {
                "topic": f"The Deadliest Animal Olympic Record You Never Heard Of",
                "category": "sports",
                "premise": "Comparing elite human athletes to animal world records in velocity and power.",
                "trend_type": "EVERGREEN",
                "velocity": "HIGH",
                "source_signal": "Sports Physiology",
            }
        ]

    def _infer_category(self, text: str) -> str:
        """Heuristically infer content category from text."""
        lower = text.lower()
        if any(w in lower for w in ["game", "playstation", "xbox", "nintendo", "gta", "steam"]):
            return "gaming"
        if any(w in lower for w in ["nfl", "nba", "fifa", "premier league", "match", "goal", "champion", "f1", "ufc", "ronaldo", "scoring"]):
            return "sports"
        if any(w in lower for w in ["movie", "actor", "hollywood", "netflix", "trailer", "grammy", "oscar", "album"]):
            return "entertainment"
        if any(w in lower for w in ["ai", "robot", "apple", "google", "software", "chip", "nvidia", "quantum"]):
            return "technology"
        if any(w in lower for w in ["planet", "nasa", "star", "galaxy", "telescope", "orbit", "mars"]):
            return "space"
        if any(w in lower for w in ["funny", "hilarious", "joke", "meme", "bizarre", "absurd"]):
            return "humor"
        if any(w in lower for w in ["war", "ancient", "emperor", "century", "president", "archaeology"]):
            return "history"
        if any(w in lower for w in ["animal", "shark", "bear", "creature", "species", "evolution"]):
            return "animals"
        return "news"

    def _get_universal_fallback_bank(self) -> List[Dict[str, Any]]:
        """Multi-category universal topic repository ensuring rich options across niches."""
        return [
            # News / Unusual
            {"topic": "The City Where Cats Legally Outnumber Humans", "category": "geography", "premise": "On Aoshima Island, felines reign supreme with a 6-to-1 ratio.", "trend_type": "EVERGREEN", "velocity": "STEADY", "source_signal": "Global Geography"},
            # Sports
            {"topic": "The 100-Meter Sprint Record That Scientists Say Is Physically Impossible to Beat", "category": "sports", "premise": "Biomechanics calculations show human tendons reach fracture limit at 9.27s.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Sports Biomechanics"},
            # Entertainment
            {"topic": "The Bizarre Sound Effect Used In Literally 400 Famous Movies", "category": "entertainment", "premise": "The legendary Wilhelm Scream origin and why Hollywood sound designers refuse to retire it.", "trend_type": "EVERGREEN", "velocity": "STEADY", "source_signal": "Cinema Archives"},
            # Humor
            {"topic": "The Most Unsuccessful Bank Robbery in Recorded History", "category": "humor", "premise": "A thief who entered through an automatic exit door and locked himself inside.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Historical Satire"},
            # Cartoons / Animation
            {"topic": "Byte & Sam: What Happens When an AI Cleans Your Room", "category": "cartoons", "premise": "Byte reorganizes the apartment by atomic weight, confusing Sam completely.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Original Cartoon Engine"},
            # Science
            {"topic": "Why Boiling Water Poured Into Extreme Cold Freezes Faster Than Cold Water", "category": "science", "premise": "The Mpemba Effect: how hydrogen bonds defy standard thermodynamics.", "trend_type": "EVERGREEN", "velocity": "RISING", "source_signal": "Physical Chemistry"},
            # History
            {"topic": "The 335-Year War With Zero Casualties", "category": "history", "premise": "The bloodless conflict between the Netherlands and the Isles of Scilly forgotten for over 3 centuries.", "trend_type": "EVERGREEN", "velocity": "STEADY", "source_signal": "Historical Curiosities"},
            # Technology
            {"topic": "Why Modern Submarines Still Use Xbox Controllers to Steer Periscopes", "category": "technology", "premise": "Military engineers replaced $38,000 joysticks with $30 gamepads for superior ergonomic speed.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Military Tech"},
            # Gaming
            {"topic": "The Unbeatable Level in Mario That Took Supercomputers 14 Years to Solve", "category": "gaming", "premise": "Computational complexity theory proves Super Mario Bros is mathematically NP-hard.", "trend_type": "EVERGREEN", "velocity": "STEADY", "source_signal": "Game Theory"},
            # Animals
            {"topic": "The Bird That Literally Impales Its Prey on Barbed Wire Like a Butcher", "category": "animals", "premise": "The Loggerhead Shrike uses environmental thorns to store food for later.", "trend_type": "EVERGREEN", "velocity": "STEADY", "source_signal": "Evolutionary Biology"},
            # Mystery
            {"topic": "The Mysterious Humming Sound in Taos That Driven Residents Crazy", "category": "mystery", "premise": "The Taos Hum: a persistent low-frequency drone heard by only 2% of the population.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Acoustic Phenomena"},
            # Food
            {"topic": "Why McDonald's Ice Cream Machines Are Literally Designed to Break", "category": "food", "premise": "The complex automated 4-hour heat pasteurization cycle and right-to-repair battle.", "trend_type": "TRENDING", "velocity": "RISING", "source_signal": "Food Engineering"},
            # Space
            {"topic": "Why Astronauts Return From Space Two Inches Taller", "category": "space", "premise": "Zero gravity decompresses spinal discs, but gravity violently snaps them back upon return.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Aerospace Medicine"},
            # Original Fiction
            {"topic": "What If Gravity Turned Off For Exactly 5 Seconds Worldwide?", "category": "original fiction", "premise": "Atmospheric pressure, unbolted vehicles, and orbital mechanics in 5 chaotic seconds.", "trend_type": "EVERGREEN", "velocity": "HIGH", "source_signal": "Scientific Fiction"},
        ]


TrendIntelligenceEngine = UniversalTrendEngine
trend_engine = UniversalTrendEngine()

