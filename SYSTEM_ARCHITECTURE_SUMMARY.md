# SensorySlice: Full Architecture & Development Summary

*This file serves as a complete memory bank of everything we built, customized, and integrated. Reference this file when updating or adding new features.*

## 1. The Core Objective
We successfully merged 10 separate GitHub repositories (like `dramaclaw`, `HeyGem.ai`, `stickman-video-director`, `youtube-automation-agent`) into a **single, unified, fully autonomous YouTube Shorts AI Studio**. The agent runs completely free of charge.

## 2. The 4 Visual Render Pipelines
Instead of being locked into one video style, the AI uses a `CreativeDirectorAgent` to dynamically route scripts to one of four distinct visual pipelines based on the topic:

1. **CinematicPipeline (`dramaclaw`)**: 
   - Uses Pexels API to pull high-end, copyright-free stock footage.
   - Applies deep color grading, cinematic letterboxing (black bars), and Ken Burns motion.
   - Used for History, Space, and Documentary topics.
2. **HyperframesPipeline (`Web Render`)**: 
   - Uses headless `Playwright` to render dynamic HTML/CSS templates (Reddit style, HackerNews style).
   - Animates the DOM into frames and stitches them using FFmpeg.
   - Used for Technology, News, and Social topics.
3. **WhiteboardPipeline (`Stickman/Doodle`)**: 
   - Uses Pollinations AI (`nologo=true` with a 60px bottom crop to remove watermarks).
   - Generates minimal stickman and whiteboard illustrations.
4. **CartoonPipeline (`3D Animation`)**: 
   - Uses Pollinations AI with a specific Pixar/3D aesthetic prompt.
   - Both image pipelines use FFmpeg to pan/zoom and overlay ASS subtitles.

## 3. The Dual-LLM Intelligence Engine
- **Brainstorming (Gemini 1.5 Flash)**: The `trend_engine` scrapes real-time internet feeds (HackerNews, Google Trends). If the feeds are slow, it falls back to Gemini to hallucinate 10-15 completely novel, obscure topic ideas. 
- **Scripting (Groq Llama-3)**: We use Groq's blazing-fast free tier (14,400 requests/day) to write the actual scripts, generate hooks, and score opportunities across 13 dimensions.
- **Anti-Repetition Engine**: The AI generates a mathematical vector embedding of every video it makes and stores it in a `TurboVec` database. If a new topic has a semantic distance of < 0.2 to an old video, it immediately discards it, guaranteeing 100% unique topics forever.

## 4. The 3-Tier Audio Engine
1. **Tier 1 (VoiceStudio)**: Local OpenAI-compatible high-end voices (`alloy`, `nova`, etc.).
2. **Tier 2 (Edge-TTS)**: Microsoft's cloud neural voices (13+ high-quality accents).
3. **Tier 3 (Offline pyttsx3)**: Standard Windows voices as an absolute safety net.
- **Procedural Background Music**: If no `.mp3` is found in the `assets/music` folder, the agent literally synthesizes a 45-second ambient harmonic pad from scratch using FFmpeg sine waves.

## 5. Deployment & Scheduling
- **YouTube API**: We implemented `publishAt` scheduling. The agent auto-uploads 2 Shorts daily and 2 Long videos weekly.
- **Telegram Integration**: The agent automatically uploads the final rendered `.mp4` video directly to your Telegram bot via the Telegram API (falling back to a text message if the video exceeds Telegram's 50MB bot limit).
- **GitHub Actions**: We created a master workflow (`Autonomous Video Generation` in `.github/workflows/generate-video.yml`). It runs autonomously on Microsoft's servers, checking out the code, installing Playwright dependencies, synthesizing the video, and deploying it. Old legacy workflows were deleted to prevent API limits from being exhausted.

## 6. How to Run Locally
```bash
python app.py run-agent
```

## 7. How to Update Tomorrow
- **To add a new visual style**: Create a new class in `backend/creative/pipelines/` inheriting from `BasePipeline`, and register it in `backend/creative/pipelines/registry.py`.
- **To add a new topic category**: Update `hybrid_combinations` in `backend/intelligence/content_portfolio.py`.
- **To change the voice**: Edit the default voice or engine in `backend/core/config.py`.
