"""Models package for YouTube Shorts Agent"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectState(str, Enum):
    IDEA = "IDEA"
    RESEARCHING = "RESEARCHING"
    RESEARCHED = "RESEARCHED"
    SCRIPTING = "SCRIPTING"
    SCRIPT_READY = "SCRIPT_READY"
    FACT_CHECKING = "FACT_CHECKING"
    FACT_CHECKED = "FACT_CHECKED"
    VOICE_GENERATING = "VOICE_GENERATING"
    VOICE_READY = "VOICE_READY"
    VISUALS_COLLECTING = "VISUALS_COLLECTING"
    VISUALS_READY = "VISUALS_READY"
    EDITING = "EDITING"
    RENDERED = "RENDERED"
    QC_RUNNING = "QC_RUNNING"
    QC_PASSED = "QC_PASSED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    CANCELLED = "CANCELLED"


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNCERTAIN = "UNCERTAIN"
    CONTRADICTED = "CONTRADICTED"


class ResearchSource(BaseModel):
    url: str
    title: str
    extract: str
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class FactualClaim(BaseModel):
    claim_text: str
    status: ClaimStatus = ClaimStatus.UNCERTAIN
    confidence: float = 0.5
    evidence: str = ""
    source_url: Optional[str] = None


class FactCheckReport(BaseModel):
    overall_confidence: float
    claims: List[FactualClaim] = Field(default_factory=list)
    passed: bool
    notes: str = ""


class ScriptScene(BaseModel):
    scene_index: int
    narration: str
    duration_est: float = 4.0
    visual_description: str
    visual_path: Optional[str] = None
    transition: str = "fade"


class ScriptModel(BaseModel):
    hook: str
    context: str
    main_facts: str
    payoff: str
    cta: str = ""
    full_narration: str
    word_count: int
    estimated_duration_sec: float
    scenes: List[ScriptScene] = Field(default_factory=list)


class VisualAsset(BaseModel):
    asset_id: str
    file_path: str
    source_url: str
    source_name: str
    license: str = "Public Domain / CC"
    creator: str = "Unknown"
    attribution_required: bool = False
    is_procedural: bool = False


class VideoQCReport(BaseModel):
    passed: bool
    quality_score: int  # 0 to 100
    technical_passed: bool
    audio_passed: bool
    captions_passed: bool
    content_passed: bool
    issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class YouTubeMetadata(BaseModel):
    titles: List[str] = Field(default_factory=list)
    selected_title: str
    description: str
    hashtags: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    pinned_comment: str = ""


class ProjectModel(BaseModel):
    id: str
    title: str
    category: str
    state: ProjectState = ProjectState.IDEA
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    video_path: Optional[str] = None
    duration_sec: Optional[float] = None
    quality_score: Optional[int] = None
    youtube_url: Optional[str] = None
    auto_publish: bool = False
    repair_attempts: int = 0
    error_message: Optional[str] = None
