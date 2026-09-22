# Development Memory Log - Sept 15, 2026

This file serves as a local memory bank recording the massive architectural upgrades applied to the SensorySlice project today.

## 1. Project Health & Bug Fixes
- **Subtitle Bug Fix:** The user reported subtitles were hidden behind the YouTube UI. I fixed `whisper_service.py` by changing the ASS alignment to 5 (Middle-Center) with MarginV 0, perfectly placing the text in the safe zone.
- **Voice Variety:** Added 6 new premium neural voices to `tts_service.py` and implemented randomized selection to prevent the channel from sounding repetitive.
- **Metadata JSON Bug:** Fixed a critical bug in `metadata_agent.py` and `script_writer.py` where the LLM wrapped outputs in markdown code blocks, causing JSON parsing to fail and default to the hardcoded "burning space steak" topic. Added a robust regex stripper.

## 2. Advanced Agent Capabilities Integration
The user provided a list of state-of-the-art AI repositories. Based on a strategic analysis, I integrated the top 3 frameworks:
- **`browser-use`**: Added to `research_service.py`. The agent now spawns an autonomous browser to scrape deep facts from Reddit and ScienceDaily, falling back to Wikipedia if no API key is provided.
- **`agentmemory`**: Added to `trend_scout.py`. Replaced the custom text-matching algorithm with a true vector embedding search (`distance < 0.2`) to mathematically prevent duplicate topics from being generated.
- **`scientific-agent-skills`**: Injected strict peer-review prompts into `fact_checker.py` to enforce rigorous scientific validation of all LLM claims.

## 3. Viral Visual & Auditory Enhancements
To ensure maximum viewer retention (TikTok/Shorts style):
- **Ken Burns Motion:** Fixed the crashing zoom filter in `ffmpeg_service.py` and implemented dynamic randomized panning (zoom_in, zoom_out, pan_left, pan_right) for all static AI imagery.
- **Hormozi-Style Captions:** Rewrote the ASS caption generator in `whisper_service.py` to drop the old karaoke sweep and instead implement discrete, word-level highlighting (bright yellow, larger font) as each word is spoken.
- **Procedural SFX:** Added a 3-track audio mix to `ffmpeg_service.py` that injects a procedural white/pink noise "impact/whoosh" sound effect into the first 1.5 seconds of every video to instantly hook viewers.

## 4. CI/CD & Deployment Fixes
- **GitHub Actions Compatibility:** Discovered that the Ubuntu cloud runners would fail to launch the new `browser-use` agent because the Chromium binaries were missing. Updated `.github/workflows/daily_shorts.yml` and `.github/workflows/agent_cron.yml` to run `playwright install --with-deps chromium` before executing the agent, guaranteeing flawless automation in the cloud.

## 5. Automation-Ready Video Pipelines (Sept 22, 2026)
- **Skeletal Stickman Engine:** Created a completely Python-native procedural animation engine (`stickman_pipeline.py`) that uses `Pillow` to generate frames (bobbing heads, talking mouths, typewriter text) and stitches them natively into `.mp4` files via FFmpeg.
- **Manim Educational Engine:** Built a `manim_pipeline.py` script that generates clean, 3Blue1Brown-style vector animations using the Manim CLI. 
- **Compositing Logic:** Re-engineered `ffmpeg_service.py` to seamlessly handle both static `.jpg` assets (applying Ken Burns) and actual `.mp4` video clips (looping/scaling them to the voiceover).
- **HuggingFace FLUX Image Generation:** Upgraded the procedural image generation in `asset_service.py` from Pollinations to `FLUX.1-schnell` via the HuggingFace Inference API, producing immensely higher quality assets. Also added robust environment variable loading using `python-dotenv` in `config.py`.
- **Orchestrator Control Fix:** Fixed a bug in `orchestrator.py` where providing an explicit `--topic` argument was ignored because the system defaulted to `AUTONOMOUS` mode. Now, explicit prompts instantly override the trend scout.
- **GitHub Actions Update:** Updated `generate-video.yml` with dependencies (`libcairo2-dev`, `libpango1.0-dev`), added the `HF_API_KEY` secret, and modified the matrix run steps to inject the desired `VisualTreatment` style directly into the `--topic` flag.

## Current State
The pipeline is fully autonomous, extremely resilient, and capable of rendering highly engaging, retention-optimized videos with zero human input. All code is pushed and synced with GitHub.
