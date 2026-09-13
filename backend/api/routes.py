"""
FastAPI Routes for YouTube Shorts Automation Dashboard & REST API.
Provides control over generation, inspection, review, and publishing.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.core.config import settings, PROJECTS_DIR, BASE_DIR
from backend.core.database import (
    delete_project_record,
    get_assets,
    get_claims,
    get_latest_qc_result,
    get_project,
    get_research_sources,
    get_script,
    list_jobs,
    list_projects,
    update_project_state,
)
from backend.core.jobs import job_manager
from backend.core.logging import logger
from backend.core.orchestrator import orchestrator
from backend.models import ProjectModel, ProjectState
from backend.services.ffmpeg_service import ffmpeg_service
from backend.services.llm_service import llm_service
from backend.services.youtube_service import youtube_service
from backend.learning.content_brain import content_brain
from backend.learning.daily_review import daily_review_agent
from backend.learning.comment_engine import comment_engine

app = FastAPI(title="YouTube Shorts Autonomous Agent", version="2.0.0")

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    topic: Optional[str] = None
    category: Optional[str] = None
    auto_publish: Optional[bool] = False
    character: Optional[str] = None
    format: Optional[str] = None


class BlacklistRequest(BaseModel):
    list_type: str  # "category", "topic", "keyword", "source"
    value: str
    reason: Optional[str] = ""


class CharacterRequest(BaseModel):
    name: str
    persona: str
    visual_style: str
    catchphrase: Optional[str] = ""


class CommentSubmissionRequest(BaseModel):
    comments: List[Dict[str, str]]  # [{"text": "...", "author": "..."}]



# ==========================================
# System Health & Status
# ==========================================

@app.get("/api/status")
def get_system_status() -> Dict[str, Any]:
    """Retrieve runtime statuses of all core subsystem dependencies."""
    ollama_ok = llm_service.is_available()
    models = llm_service.list_installed_models() if ollama_ok else []
    
    return {
        "status": "online",
        "demo_mode": settings.demo_mode,
        "auto_publish": settings.auto_publish,
        "ffmpeg": {
            "available": True,
            "path": ffmpeg_service.ffmpeg_path,
        },
        "ollama": {
            "connected": ollama_ok,
            "base_url": settings.ollama_base_url,
            "configured_model": settings.ollama_model,
            "active_model": llm_service.get_best_available_model(),
            "installed_models": models,
        },
        "tts": {
            "engine": settings.tts_engine,
            "voice": settings.tts_voice,
        },
        "youtube": {
            "authenticated": youtube_service.is_authenticated(),
            "client_secrets_exists": settings.youtube_client_secrets_file.exists(),
            "privacy_default": settings.youtube_privacy_status,
        },
        "video_spec": {
            "width": settings.video_width,
            "height": settings.video_height,
            "fps": settings.video_fps,
            "target_wpm": settings.target_words_per_minute,
        },
    }


# ==========================================
# Project Management Endpoints
# ==========================================

@app.get("/api/projects")
def get_all_projects() -> List[Dict[str, Any]]:
    """Return all projects sorted by creation date."""
    projects = list_projects(limit=100)
    result = []
    for p in projects:
        p_dict = p.model_dump()
        # Add relative stream URL if video exists
        video_exists = (p.video_path and os.path.exists(p.video_path)) or (PROJECTS_DIR / p.id / "render" / "final.mp4").exists()
        if video_exists:
            p_dict["stream_url"] = f"/media/{p.id}/render/final.mp4"
        result.append(p_dict)
    return result


@app.get("/api/projects/{project_id}")
def get_project_details(project_id: str) -> Dict[str, Any]:
    """Fetch complete project intelligence: script, claims, assets, QC, video."""
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    script = get_script(project_id)
    sources = get_research_sources(project_id)
    claims = get_claims(project_id)
    assets = get_assets(project_id)
    qc = get_latest_qc_result(project_id)

    # Read metadata JSON if present
    meta_path = PROJECTS_DIR / project_id / "metadata" / "youtube_metadata.json"
    metadata = {}
    if meta_path.exists():
        import json
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    # Read SOURCES.md if present
    sources_md_path = PROJECTS_DIR / project_id / "SOURCES.md"
    sources_md = ""
    if sources_md_path.exists():
        with open(sources_md_path, "r", encoding="utf-8") as f:
            sources_md = f.read()

    video_exists = (proj.video_path and os.path.exists(proj.video_path)) or (PROJECTS_DIR / project_id / "render" / "final.mp4").exists()

    return {
        "project": proj.model_dump(),
        "script": script.model_dump() if script else None,
        "sources": [s.model_dump() for s in sources],
        "claims": [c.model_dump() for c in claims],
        "assets": [a.model_dump() for a in assets],
        "qc": qc.model_dump() if qc else None,
        "metadata": metadata,
        "sources_markdown": sources_md,
        "stream_url": f"/media/{project_id}/render/final.mp4" if video_exists else None,
    }


@app.post("/api/generate")
def start_generation(payload: GenerateRequest) -> Dict[str, str]:
    """Enqueue an autonomous YouTube Shorts production job."""
    job_id = job_manager.submit_generation_job(
        topic=payload.topic,
        category=payload.category,
        auto_publish=payload.auto_publish,
    )
    return {
        "message": "Generation job enqueued successfully",
        "job_id": job_id,
    }


@app.post("/api/projects/{project_id}/approve")
def approve_project(project_id: str) -> Dict[str, str]:
    """Approve a video that was awaiting human review."""
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    update_project_state(project_id, ProjectState.APPROVED)
    return {"message": f"Project '{project_id}' approved successfully"}


@app.post("/api/projects/{project_id}/publish")
def publish_project(project_id: str, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Trigger YouTube upload for an approved project."""
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    if not proj.video_path or not os.path.exists(proj.video_path):
        raise HTTPException(status_code=400, detail="Rendered video not found")

    meta_path = PROJECTS_DIR / project_id / "metadata" / "youtube_metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=400, detail="Metadata missing")

    import json
    with open(meta_path, "r", encoding="utf-8") as f:
        mdata = json.load(f)

    from backend.models import YouTubeMetadata
    from backend.agents.publisher import publisher_agent

    metadata_obj = YouTubeMetadata(**mdata)

    def _do_upload():
        publisher_agent.publish_short(proj, metadata_obj)

    background_tasks.add_task(_do_upload)
    return {"message": f"Publish task started for '{project_id}'"}


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str) -> Dict[str, str]:
    """Delete a project and its rendered files."""
    delete_project_record(project_id)
    proj_dir = PROJECTS_DIR / project_id
    if proj_dir.exists():
        import shutil
        shutil.rmtree(proj_dir, ignore_errors=True)
    return {"message": f"Project '{project_id}' deleted"}


@app.get("/api/jobs")
def get_jobs():
    """Retrieve status of background jobs."""
    return list_jobs(limit=30)


# ==========================================
# Media Streaming Endpoint
# ==========================================

@app.get("/media/{project_id}/{subpath:path}")
def stream_media(project_id: str, subpath: str):
    """Safely stream rendered video or asset media files."""
    try:
        base_dir = PROJECTS_DIR.resolve()
        media_file = (base_dir / project_id / subpath).resolve()
        # Security: prevent path traversal outside project dir (case-insensitive for Windows)
        if not str(media_file).lower().startswith(str(base_dir).lower()):
            raise HTTPException(status_code=403, detail="Forbidden")
    except Exception:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not media_file.exists():
        raise HTTPException(status_code=404, detail="Media file not found")

    return FileResponse(media_file, media_type="video/mp4")


# ==========================================
# Content Brain & Learning Intelligence Endpoints
# ==========================================

@app.get("/api/brain")
def get_content_brain_status() -> Dict[str, Any]:
    """Retrieve full status of persistent Content Brain."""
    return content_brain.get_status()


@app.get("/api/brain/categories")
def get_categories() -> List[Dict[str, Any]]:
    """Retrieve category performance leaderboard."""
    return content_brain.get_category_leaderboard()


@app.get("/api/brain/characters")
def get_characters() -> List[Dict[str, Any]]:
    """Retrieve recurring channel characters (Byte & Sam)."""
    return content_brain.get_all_characters()


@app.post("/api/brain/characters")
def add_character(req: CharacterRequest) -> Dict[str, str]:
    """Add or update a recurring character."""
    content_brain.add_recurring_character(
        name=req.name,
        persona=req.persona,
        visual_style=req.visual_style,
        catchphrase=req.catchphrase or "",
    )
    return {"message": f"Character '{req.name}' saved to Content Brain."}


@app.get("/api/brain/blacklists")
def get_blacklists() -> List[Dict[str, Any]]:
    """Retrieve active human override blacklists."""
    return content_brain.get_active_blacklists()


@app.post("/api/brain/blacklists")
def add_blacklist(req: BlacklistRequest) -> Dict[str, Any]:
    """Add human override blacklist rule (topic, category, keyword, source)."""
    success = content_brain.add_override_blacklist(
        list_type=req.list_type,
        value=req.value,
        reason=req.reason or "",
    )
    if not success:
        raise HTTPException(status_code=400, detail="Could not add blacklist rule.")
    return {"message": f"Blacklisted {req.list_type}: '{req.value}'"}


@app.get("/api/brain/reviews")
def get_reviews(limit: int = 7) -> List[Dict[str, Any]]:
    """Retrieve recent nightly self-learning reviews."""
    return content_brain.get_recent_reviews(limit=limit)


@app.post("/api/brain/reviews/run")
def trigger_daily_review() -> Dict[str, Any]:
    """Run an on-demand self-learning review immediately."""
    result = daily_review_agent.run_review()
    return result.to_dict()


@app.get("/api/brain/comments")
def get_comment_topics() -> List[Dict[str, Any]]:
    """Retrieve pending topic ideas derived from viewer comments."""
    return comment_engine.get_pending_topics()


@app.post("/api/brain/comments")
def submit_viewer_comments(req: CommentSubmissionRequest) -> Dict[str, Any]:
    """Parse incoming viewer comments into new topic candidates."""
    candidates = comment_engine.process_incoming_comments(req.comments)
    return {
        "processed": len(req.comments),
        "derived_candidates": [c.to_dict() for c in candidates],
    }


# ==========================================
# Static Dashboard Frontend Mounting
# ==========================================


FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
