# ⚡ Autonomous Zero-Paid-API YouTube Shorts Agent

A production-grade, local-first autonomous AI production agent that discovers viral curiosity topics, conducts factual research on free public APIs, writes retention-engineered scripts, fact-checks assertions, synthesizes neural voiceover, collects public domain & procedural visual assets, composes 9:16 vertical 1080x1920 30FPS MP4 videos with FFmpeg, burns in animated captions, mixes and ducks background music, executes comprehensive Quality Control, and manages publishing through official YouTube Data API.

**Absolute Cost Requirement**: Operates with **$0 paid APIs, $0 monthly AI subscriptions, $0 paid TTS, $0 paid video APIs**.

---

## 🌟 Architecture & Workflow

```
USER CONFIGURATION
      ↓
TOPIC DISCOVERY (TrendScoutAgent)
      ↓
TOPIC EVALUATION (TopicEvaluatorAgent: Novelty, Curiosity, Educational Value, Hook, Visuals)
      ↓
RESEARCH (TopicResearchAgent / Wikipedia REST & Public APIs)
      ↓
HOOK GENERATION (HookAgent: 0–3s retention hook)
      ↓
SCRIPT GENERATION (ScriptWriterAgent: 130–160 WPM, strictly structured)
      ↓
FACT CHECKING (FactCheckerAgent: assertion extraction & threshold confidence scoring)
      ↓
VOICEOVER (VoiceAgent: edge-tts neural voice & pyttsx3 offline fallback)
      ↓
VISUALS (VisualResearchAgent: Wikimedia Commons / CC0 procedural generation)
      ↓
CAPTIONS (CaptionAgent: ASS/SRT subtitles styled for YouTube Shorts safe zone)
      ↓
VIDEO EDITING (VideoEditorAgent: FFmpeg 1080x1920 9:16 30FPS Ken Burns & music ducking)
      ↓
QUALITY CONTROL (QualityControlAgent: technical, audio, captions, content checks & self-repair)
      ↓
METADATA (MetadataAgent: 5 titles, descriptions, hashtags, tags, pinned comment)
      ↓
HUMAN APPROVAL / AUTO-PUBLISH (PublisherAgent: official YouTube OAuth2)
```

---

## 💻 Requirements

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: 3.10 to 3.12.
- **FFmpeg**: Bundled automatically via `imageio-ffmpeg` or detected from system PATH.
- **Ollama**: Locally running Ollama (`http://localhost:11434`) with model (e.g., `qwen2.5:3b`, `gemma4`, `llama3.2`).

---

## 🚀 Quick Start (Exact Commands)

### 1. Set Up Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Verify Environment With Setup Wizard
```powershell
python app.py setup
```
Expected output:
```text
============================================================
 AUTONOMOUS YOUTUBE SHORTS AGENT - SETUP WIZARD
============================================================
[OK] Python detected: v3.12.10
[OK] FFmpeg detected: .../ffmpeg-win-x86_64-v7.1.exe
[OK] Ollama connected: http://localhost:11434
[OK] Ollama models available: qwen2.5:3b, gemma4:latest
[OK] Active model selected: qwen2.5:3b
[OK] TTS Engine configured: edge-tts (Voice: en-US-ChristopherNeural)
[OK] Projects workspace: .../projects
[OK] Royalty-free music library: .../assets/music
[!] YouTube OAuth not configured (Video generation works 100% locally).
============================================================
 System is fully ready for autonomous Shorts production!
 Run: 'python app.py run-agent' to produce your first video.
============================================================
```

### 3. Launch Web Studio Dashboard
```powershell
python app.py dashboard
```
Open your browser to: **`http://127.0.0.1:8000/`**

### 4. Produce Your First Short (One-Click CLI)
```powershell
# Autonomous topic discovery and generation:
python app.py run-agent

# Or target a specific test topic:
python app.py run-agent --topic "Why does space smell like something burning?"
```

---

## ⚙️ Free Local Components vs Optional YouTube Integration

| Component | Provider / Tool | Cost | Auth Required? |
| :--- | :--- | :--- | :--- |
| **Local LLM** | Ollama (`qwen2.5:3b`) | **$0** | No API Key |
| **Video Engine** | FFmpeg 7.1 (`imageio-ffmpeg`) | **$0** | No API Key |
| **TTS Engine** | Microsoft Edge Neural (`edge-tts`) / pyttsx3 | **$0** | No API Key |
| **Fact Research** | Wikipedia REST API & Wikimedia | **$0** | No API Key |
| **Subtitles** | Advanced SubStation Alpha (`.ass`) & SRT | **$0** | No API Key |
| **Visual Fallback** | Pillow Procedural Graphics Engine | **$0** | No API Key |
| **Background Audio** | Ambient Harmonic Synthesis | **$0** | No API Key |
| **YouTube Upload** | Google YouTube Data API v3 | **$0** | OAuth2 Client Secrets |

---

## 📺 YouTube Publishing Configuration

Video generation is **100% functional locally without YouTube credentials**.
When you are ready to publish videos to your YouTube channel:

1. Visit [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **YouTube Data API v3**.
3. Under **Credentials**, create an **OAuth 2.0 Client ID** (Desktop Application).
4. Download the JSON file and save it to:
   ```text
   credentials/client_secrets.json
   ```
5. On first upload, the application will open your browser for one-time Google authorization.
6. The authorization token is saved securely in `credentials/token.pickle` (gitignored).
7. Default privacy status is strictly `private` to avoid accidental public publishing.

---

## 🧪 Testing & Verification

Run the automated test suite:
```powershell
pytest tests/ -v
```
The test suite tests:
- Configuration parsing and environmental overrides (`tests/test_config.py`)
- SQLite database integrity, topic memory deduplication, claims, scripts (`tests/test_database.py`)
- Specialized agent logic: TrendScout, TopicEvaluator, HookAgent, ScriptWriter, FactChecker, QualityControl (`tests/test_agents.py`)
- Core services: FFmpeg resolution, procedural visuals, subtitle generators, Wikipedia research (`tests/test_services.py`)
- FastAPI REST endpoints (`tests/test_api.py`)

---

## 📁 Project File Structure

```text
d:\aiworksspace\vido\
├── app.py                     # Unified CLI and Studio launcher
├── requirements.txt           # Pinned dependency requirements
├── .env.example               # Configuration template
├── .gitignore                 # Secrets, media, and DB ignore rules
├── README.md                  # Comprehensive operating documentation
├── sample.mp4                 # Validated 1080x1920 30FPS sample Short
├── sample_script.txt          # Verified narration script
├── sample_sources.md          # Complete sources and licensing record
├── sample_metadata.json       # Generated titles, hashtags, description
├── backend/
│   ├── core/
│   │   ├── config.py          # Centralized configuration & defaults
│   │   ├── database.py        # Thread-safe SQLite schema & CRUD
│   │   ├── logging.py         # Structured logging
│   │   ├── orchestrator.py    # State machine & auto-repair loop
│   │   └── jobs.py            # Async background job queue
│   ├── agents/
│   │   ├── trend_scout.py     # Topic discovery & memory deduplication
│   │   ├── topic_evaluator.py # 8-dimension engagement evaluation
│   │   ├── researcher.py      # Wikipedia research & HookAgent
│   │   ├── script_writer.py   # 130-160 WPM Shorts script writer
│   │   ├── fact_checker.py    # Claim verification & confidence scoring
│   │   ├── voice_agent.py     # Neural speech synthesis & normalization
│   │   ├── visual_agent.py    # Asset acquisition & procedural fallback
│   │   ├── caption_agent.py   # Synchronized ASS subtitle formatting
│   │   ├── video_editor.py    # FFmpeg 9:16 composition & audio ducking
│   │   ├── metadata_agent.py  # Titles, hashtags, tags, descriptions
│   │   ├── quality_control.py # Technical & content QC inspection
│   │   ├── publisher.py       # Official YouTube upload & demo mode
│   │   └── scheduler.py       # Recurring daily task scheduler
│   ├── services/
│   │   ├── ffmpeg_service.py  # FFmpeg filtergraphs, Ken Burns, probe
│   │   ├── ollama_service.py  # Ollama connection & JSON schema mode
│   │   ├── tts_service.py     # Edge-TTS & pyttsx3 fallback
│   │   ├── research_service.py# Wikipedia & Wikimedia APIs
│   │   ├── asset_service.py   # Media downloads & procedural Pillow visuals
│   │   ├── whisper_service.py # Subtitle generation & rhythm alignment
│   │   └── youtube_service.py # Official Google OAuth2 & resumable upload
│   ├── models/
│   │   └── __init__.py        # Pydantic schemas (Project, Script, Claims, QC)
│   └── api/
│       └── routes.py          # FastAPI REST endpoints & media stream
├── frontend/
│   ├── index.html             # Studio single-page application
│   ├── styles.css             # Modern dark glassmorphism styling
│   └── app.js                 # Studio frontend controller & polling
├── projects/                  # Generated projects, scripts, renders, logs
├── assets/
│   └── music/                 # Royalty-free audio tracks
├── credentials/               # Google OAuth secrets & tokens (gitignored)
└── tests/                     # Automated pytest test suite
```

---

## 🔒 Security & Privacy

- **No Hard-coded Secrets**: Zero API keys or tokens are stored in source code.
- **Git Ignored**: `credentials/`, `tokens/`, `*.pickle`, `*.env`, `*.db` are strictly excluded from source control.
- **Safe Defaults**: `AUTO_PUBLISH=false` and `YOUTUBE_PRIVACY_STATUS=private` ensure no accidental public publishing occurs while testing.
- **Official Google OAuth2**: Uploads strictly adhere to official Google OAuth authentication guidelines.
