# Changelog

All notable changes to the Autonomous Shorts Agent will be documented in this file.

## [Unreleased]

### Added
- **Universal ZeroGPU Backend API**: Converted the experimental Mocap Hugging Face Space into a unified A100 GPU microservice for the local agent.
- **Whisper-V3 Turbo Integration**: Integrated `openai/whisper-large-v3-turbo` directly into the agent via the ZeroGPU Space. Replaced algorithmic fake word timing with true millisecond-accurate word-level timestamp generation.
- **Meta MusicGen Integration**: Deployed `facebook/musicgen-small` into the ZeroGPU space and updated `asset_service.py` and `video_editor.py` to prompt custom, royalty-free background music dynamically tuned to the video's mood and exact duration.
- **Hugging Face Hub Deployment Script**: Created `deploy_space.py` to seamlessly update the ZeroGPU space code directly from the local repository.
- **Self-Improving Memory Logging**: Documented that the self-improvement loop (`daily_review_agent`) is already natively active in `orchestrator.py`, adjusting topic weight allocations automatically after every video generation.

### Fixed
- **Black Video Bug in Mocap Pipeline**: Modified `mocap_pipeline.py` to use a copy of the sourced visual footage as a fallback rather than defaulting to a black frame when the Blender Engine is absent locally.

### Changed
- **Asset Service Validation**: Verified that `asset_service.py` is fully wired to use the Hugging Face Serverless API (`FLUX.1-schnell`) out-of-the-box for generating photorealistic images when `HF_API_KEY` is present.
