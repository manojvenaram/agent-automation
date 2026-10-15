# SPEC.md — Project Specification

> **Status**: `FINALIZED`
>
> ⚠️ **Planning Lock**: Specification verified and active for vido.

## Vision
SensorySlice (`vido`) is a 100% autonomous, zero-cost, self-improving media company and content production engine that generates, edits, voices, reviews, and publishes viral, retention-engineered YouTube Shorts and TikToks with zero human intervention.

## Goals
1. **End-to-End Autonomous Content Pipeline** — Continuously discover trending topics across public internet signals (Google Trends, Reddit, Wikipedia, HackerNews, DuckDuckGo), generate high-retention scripts, synthesize neural voices (Edge TTS), render dynamic 9:16 visuals, generate synchronized captions, and publish directly to YouTube.
2. **Scientific Fact-Checking & Guardrails** — Enforce rigorous peer-review verification on all factual claims with an autonomous self-repair loop that rewrites conflicting claims before rendering.
3. **Closed-Loop Self-Improving Brain** — Record video performance, retention simulations, and QC reports into persistent SQLite/TurboVec memory, running daily reviews that dynamically adjust category weights, hook archetypes, and script formulas.

## Non-Goals (Out of Scope)
- Relying on paid SaaS APIs or per-generation fees (pure zero-dollar stack using free tiers, HuggingFace ZeroGPU, and local Python pipelines).
- Manual per-video video editing timelines or GUI-only workflows.
- Low-effort static image slideshows without retention pacing, motion, or audio sound design.

## Constraints
- **Zero API Cost**: Exclusively use free-tier Gemini API, HuggingFace serverless / ZeroGPU, Edge TTS, and local FFmpeg/Pillow/Manim rendering.
- **Duration & Aspect Ratio**: Output vertical video strictly in 9:16 aspect ratio (1080x1920), under 60 seconds (target 30-45s) at 130-160 words per minute.
- **Safety & Copyright**: Strictly royalty-free audio, CC/public domain visual assets, and strict blacklists preventing controversial, graphic, or spam content.

## Success Criteria
- [x] Autonomous pipeline executes end-to-end generating a ready-to-upload `.mp4` video.
- [x] Multi-agent collaboration with Director, ScriptWriter, FactChecker, and VideoEditor.
- [x] Retention-optimized psychological hooks scored against 7 viewer personas.
- [x] Multi-engine rendering support (Ken Burns cinematic, Brainrot split-screen, Stickman procedural, Manim mathematical).
- [ ] 100% test suite pass rate with resilient multi-provider LLM fallbacks.
- [ ] True closed-loop learning dynamically adapting script prompts from daily review lessons.

## User Stories

### As a YouTube Content Creator
- I want the agent to automatically scan internet trends and produce high-retention vertical shorts
- So that I can run an active, engaging YouTube channel 24/7 without spending hours scripting and editing.

### As an Audience Viewer
- I want fast-paced, scientifically accurate, visually dynamic vertical stories that hook me in 3 seconds and seamlessly loop
- So that I learn fascinating facts in under 45 seconds without boring filler.

## Technical Requirements

| Requirement | Priority | Notes |
|-------------|----------|-------|
| Multi-Source Trend Engine | Must-have | Google Trends RSS, Reddit JSON, HackerNews, Wikipedia, DuckDuckGo |
| Multi-Agent Scriptwriter | Must-have | Pacing: 0-3s hook, retention lock, visual cut escalation, infinity audio loop |
| Rigorous Fact Checker | Must-have | Claim extraction, evidence cross-referencing, automated script correction |
| Multi-Engine Video Rendering | Must-have | FFmpeg, MoviePy, Pillow procedural stickman, Manim, HuggingFace Flux |
| Neural Voice & Word Captions | Must-have | Microsoft Edge Neural TTS, Whisper word-level ASS highlighting |
| Persistent Content Brain | Must-have | SQLite database, TurboVec vector embeddings, daily review adaptation |

---

*Last updated: 2026-10-07*
