# Architecture

> SensorySlice (`vido`) Autonomous Media Engine Architecture

## Overview

SensorySlice is a modular multi-agent system operating on zero paid APIs. It orchestrates real-time internet intelligence discovery, multi-persona viewer simulation, scripted audio generation, and algorithmic FFmpeg compositing into viral 9:16 vertical videos.

```
┌────────────────────────────────────────────────────────────────────────┐
│             Trend Engine (Google Trends / Reddit / DDG / Wiki)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            Opportunity Scorer & Content Portfolio Allocator            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│       Hook Lab (10 Archetypes) & Viewer Simulator (7 Personas)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Story Engine & Script Writer (Infinity Loopback)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│          Scientific Fact Checker (Peer-Review Self-Repair Loop)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│      Media Assembly: Edge-TTS + Whisper Captions + FFmpeg / Pipelines  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│         Quality Control Agent & Auto-Publisher (YouTube / Telegram)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│      Persistent Content Brain (Daily Review & Continuous Learning)     │
└────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Intelligence & Opportunity Layer
- **Location:** `backend/intelligence/`
- **Modules:**
  - `trend_engine.py`: Scrapes Google Trends, Reddit JSON feeds, HackerNews, Wikipedia, and DuckDuckGo.
  - `opportunity_scorer.py`: Evaluates 13 predictive dimensions (0-100) and penalizes topic saturation.
  - `content_portfolio.py`: Allocates 80% proven categories / 20% experimental cross-category hybrids.

### 2. Creative & Narrative Engine
- **Location:** `backend/creative/`
- **Modules:**
  - `creative_director.py`: Selects from 20+ Shorts formats, visual treatments, and humor levels.
  - `hook_lab.py`: Generates 10+ candidate hooks across diverse psychological archetypes.
  - `viewer_simulator.py`: Simulates 7 audience personas to guarantee >80% retention score.
  - `story_engine.py`: 5 distinct narrative architectures with strict under-60s timing.

### 3. Agent Orchestration & Guardrails
- **Location:** `backend/agents/`
- **Modules:**
  - `script_writer.py`: Generates fast-paced narration with visual descriptions and audio loopback.
  - `fact_checker.py`: Extracts falsifiable claims and triggers automated repair for contradictions.
  - `voice_agent.py`: Interfaces with Edge Neural TTS voices with pitch and rate controls.
  - `video_editor.py`: Assembles video layers, background music, sound effects, and subtitles.
  - `quality_control.py`: Inspects frame integrity, audio clipping, subtitle safe-zones, and pacing.

### 4. Memory & Continuous Learning Loop
- **Location:** `backend/learning/` and `backend/memory/`
- **Modules:**
  - `content_brain.py`: Manages category weights, character evolution, blacklists, and lifetime analytics.
  - `daily_review.py`: Nightly self-review evaluating successes, failures, and strategy modifications.
  - `memory_manager.py`: Hybrid SQLite structured records + TurboVec semantic vector search.

## Data Flow

1. **Autonomous Wakeup / Trigger**: Orchestrator queries `content_portfolio` for target category.
2. **Trend Mining**: `trend_engine` discovers fresh candidate topics from live internet signals.
3. **Semantic Deduplication**: `memory_manager` checks TurboVec vector distance (< 0.25 rejected).
4. **Creative Synthesis**: `hook_lab` and `viewer_simulator` engineer the frame-1 opening hook.
5. **Scripting & Fact Checking**: `script_writer` generates scenes; `fact_checker` validates claims against research data. If discrepancies are found, an automated repair turn is executed.
6. **Audio & Subtitle Production**: `voice_agent` synthesizes neural audio; `whisper_service` aligns word-level timestamps.
7. **Visual Rendering**: Selected pipeline renders clips/frames and FFmpeg mixes video, audio, SFX, and subtitles.
8. **Quality Assurance**: `quality_control` validates file health and safe-zones.
9. **Feedback Registration**: Video metrics and QC performance are recorded into `content_brain` for the nightly learning loop.

## Conventions

- **Paths:** All persistent files stored in `data/`, project outputs in `projects/`.
- **Async & Subprocesses:** FFmpeg commands routed through `ffmpeg_service.py` with sanitized arguments.
- **Model Fallbacks:** All LLM calls pass through `llm_service.py` with multi-tier fallback cascade.

---

*Last updated: 2026-10-07*
