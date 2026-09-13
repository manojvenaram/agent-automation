"""
Database layer for YouTube Shorts Agent.
Uses SQLite with thread-safe connection pooling and automatic schema migrations.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.core.config import BASE_DIR
from backend.core.logging import logger
from backend.models import (
    ProjectModel,
    ProjectState,
    JobStatus,
    ResearchSource,
    FactualClaim,
    ScriptModel,
    ScriptScene,
    VisualAsset,
    VideoQCReport,
)

DB_PATH = BASE_DIR / "shorts_agent.db"


@contextmanager
def get_db_cursor():
    """Context manager for thread-safe SQLite cursor with WAL mode."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as err:
        conn.rollback()
        logger.error(f"Database error: {err}")
        raise err
    finally:
        conn.close()


def init_db():
    """Initialize database tables and indexes."""
    with get_db_cursor() as cur:
        # Projects table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                state TEXT NOT NULL,
                duration_sec REAL,
                quality_score INTEGER,
                video_path TEXT,
                youtube_url TEXT,
                auto_publish INTEGER DEFAULT 0,
                repair_attempts INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Topics table (with memory tracking)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                topic TEXT NOT NULL,
                category TEXT NOT NULL,
                novelty REAL DEFAULT 0.5,
                curiosity REAL DEFAULT 0.5,
                educational REAL DEFAULT 0.5,
                hook_strength REAL DEFAULT 0.5,
                factual_confidence REAL DEFAULT 0.5,
                visual_availability REAL DEFAULT 0.5,
                selected INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Research Sources table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS research_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                extract TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Factual Claims table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence TEXT,
                source_url TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Scripts table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                hook TEXT NOT NULL,
                context TEXT NOT NULL,
                main_facts TEXT NOT NULL,
                payoff TEXT NOT NULL,
                cta TEXT,
                full_narration TEXT NOT NULL,
                word_count INTEGER NOT NULL,
                estimated_duration REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Scenes table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                scene_index INTEGER NOT NULL,
                narration TEXT NOT NULL,
                duration_est REAL NOT NULL,
                visual_description TEXT,
                visual_path TEXT,
                transition TEXT DEFAULT 'fade',
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Assets table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                source_url TEXT,
                source_name TEXT,
                license TEXT,
                creator TEXT,
                attribution_required INTEGER DEFAULT 0,
                is_procedural INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # QC Results table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS qc_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                passed INTEGER NOT NULL,
                quality_score INTEGER NOT NULL,
                technical_passed INTEGER NOT NULL,
                audio_passed INTEGER NOT NULL,
                captions_passed INTEGER NOT NULL,
                content_passed INTEGER NOT NULL,
                issues_json TEXT NOT NULL,
                details_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # YouTube Uploads table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS youtube_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                privacy_status TEXT NOT NULL,
                published_url TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Background Jobs table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Settings table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Content Brain: Recurring Characters
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS characters (
                name TEXT PRIMARY KEY,
                persona TEXT NOT NULL,
                visual_style TEXT NOT NULL,
                catchphrase TEXT,
                appearances INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )

        # Content Brain: Category Performance Intelligence
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS category_scores (
                category TEXT PRIMARY KEY,
                score REAL DEFAULT 75.0,
                lifetime_videos INTEGER DEFAULT 0,
                avg_quality_score REAL DEFAULT 75.0,
                avg_retention REAL DEFAULT 70.0,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Content Brain: Analytics History
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                retention_pct REAL DEFAULT 0.0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                top_geography TEXT DEFAULT 'United States',
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """
        )

        # Content Brain: Comment-to-Content Engine
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS comment_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_text TEXT NOT NULL,
                author TEXT NOT NULL,
                derived_topic TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TEXT NOT NULL
            );
            """
        )

        # Content Brain: Daily Reviews
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_date TEXT UNIQUE NOT NULL,
                successes TEXT NOT NULL,
                failures TEXT NOT NULL,
                lessons TEXT NOT NULL,
                strategy_changes TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        # Human Overrides: Blacklists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS blacklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_type TEXT NOT NULL,
                value TEXT UNIQUE NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            );
            """
        )

        # Performance Indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_topics_topic ON topics(topic);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_claims_proj ON claims(project_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scenes_proj ON scenes(project_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blacklists_type ON blacklists(list_type);")


# ==========================================
# Project CRUD Operations
# ==========================================

def create_project(project: ProjectModel) -> None:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO projects (
                id, title, category, state, duration_sec, quality_score, 
                video_path, youtube_url, auto_publish, repair_attempts, 
                error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project.id,
                project.title,
                project.category,
                project.state.value,
                project.duration_sec,
                project.quality_score,
                project.video_path,
                project.youtube_url,
                1 if project.auto_publish else 0,
                project.repair_attempts,
                project.error_message,
                project.created_at or now,
                project.updated_at or now,
            ),
        )


def get_project(project_id: str) -> Optional[ProjectModel]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            return None
        return ProjectModel(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            state=ProjectState(row["state"]),
            duration_sec=row["duration_sec"],
            quality_score=row["quality_score"],
            video_path=row["video_path"],
            youtube_url=row["youtube_url"],
            auto_publish=bool(row["auto_publish"]),
            repair_attempts=row["repair_attempts"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def update_project_state(
    project_id: str,
    state: ProjectState,
    video_path: Optional[str] = None,
    duration_sec: Optional[float] = None,
    quality_score: Optional[int] = None,
    error_message: Optional[str] = None,
    youtube_url: Optional[str] = None,
) -> None:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            UPDATE projects 
            SET state = ?, 
                video_path = COALESCE(?, video_path),
                duration_sec = COALESCE(?, duration_sec),
                quality_score = COALESCE(?, quality_score),
                error_message = ?,
                youtube_url = COALESCE(?, youtube_url),
                updated_at = ?
            WHERE id = ?
            """,
            (
                state.value,
                video_path,
                duration_sec,
                quality_score,
                error_message,
                youtube_url,
                now,
                project_id,
            ),
        )


def increment_repair_attempt(project_id: str) -> int:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            UPDATE projects 
            SET repair_attempts = repair_attempts + 1, updated_at = ?
            WHERE id = ?
            """,
            (now, project_id),
        )
        cur.execute("SELECT repair_attempts FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        return row["repair_attempts"] if row else 0


def list_projects(limit: int = 50) -> List[ProjectModel]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        projects = []
        for row in rows:
            projects.append(
                ProjectModel(
                    id=row["id"],
                    title=row["title"],
                    category=row["category"],
                    state=ProjectState(row["state"]),
                    duration_sec=row["duration_sec"],
                    quality_score=row["quality_score"],
                    video_path=row["video_path"],
                    youtube_url=row["youtube_url"],
                    auto_publish=bool(row["auto_publish"]),
                    repair_attempts=row["repair_attempts"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return projects


def delete_project_record(project_id: str) -> None:
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM claims WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM research_sources WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM scripts WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM scenes WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM assets WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM qc_results WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM youtube_uploads WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM topics WHERE project_id = ?", (project_id,))
        cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))


# ==========================================
# Topics & Memory Operations
# ==========================================

def save_topic(
    project_id: Optional[str],
    topic: str,
    category: str,
    novelty: float = 0.5,
    curiosity: float = 0.5,
    educational: float = 0.5,
    hook_strength: float = 0.5,
    factual_confidence: float = 0.5,
    visual_availability: float = 0.5,
    selected: bool = False,
) -> int:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO topics (
                project_id, topic, category, novelty, curiosity, educational,
                hook_strength, factual_confidence, visual_availability, selected, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                topic,
                category,
                novelty,
                curiosity,
                educational,
                hook_strength,
                factual_confidence,
                visual_availability,
                1 if selected else 0,
                now,
            ),
        )
        return cur.lastrowid


def get_recent_topics(limit: int = 100) -> List[str]:
    """Retrieve recent topics from memory to prevent topic duplication."""
    with get_db_cursor() as cur:
        cur.execute("SELECT topic FROM topics ORDER BY created_at DESC LIMIT ?", (limit,))
        return [row["topic"] for row in cur.fetchall()]


# ==========================================
# Research & Claims Operations
# ==========================================

def save_research_sources(project_id: str, sources: List[ResearchSource]) -> None:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        for s in sources:
            cur.execute(
                """
                INSERT INTO research_sources (project_id, url, title, extract, retrieved_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, s.url, s.title, s.extract, s.retrieved_at or now),
            )


def get_research_sources(project_id: str) -> List[ResearchSource]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM research_sources WHERE project_id = ?", (project_id,))
        return [
            ResearchSource(
                url=row["url"],
                title=row["title"],
                extract=row["extract"],
                retrieved_at=row["retrieved_at"],
            )
            for row in cur.fetchall()
        ]


def save_claims(project_id: str, claims: List[FactualClaim]) -> None:
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM claims WHERE project_id = ?", (project_id,))
        for c in claims:
            cur.execute(
                """
                INSERT INTO claims (project_id, claim_text, status, confidence, evidence, source_url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    c.claim_text,
                    c.status.value,
                    c.confidence,
                    c.evidence,
                    c.source_url,
                ),
            )


def get_claims(project_id: str) -> List[FactualClaim]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM claims WHERE project_id = ?", (project_id,))
        return [
            FactualClaim(
                claim_text=row["claim_text"],
                status=row["status"],
                confidence=row["confidence"],
                evidence=row["evidence"] or "",
                source_url=row["source_url"],
            )
            for row in cur.fetchall()
        ]


# ==========================================
# Script & Scenes Operations
# ==========================================

def save_script(project_id: str, script: ScriptModel) -> None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT OR REPLACE INTO scripts (
                project_id, hook, context, main_facts, payoff, cta,
                full_narration, word_count, estimated_duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                script.hook,
                script.context,
                script.main_facts,
                script.payoff,
                script.cta,
                script.full_narration,
                script.word_count,
                script.estimated_duration_sec,
            ),
        )

        cur.execute("DELETE FROM scenes WHERE project_id = ?", (project_id,))
        for s in script.scenes:
            cur.execute(
                """
                INSERT INTO scenes (
                    project_id, scene_index, narration, duration_est,
                    visual_description, visual_path, transition
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    s.scene_index,
                    s.narration,
                    s.duration_est,
                    s.visual_description,
                    s.visual_path,
                    s.transition,
                ),
            )


def get_script(project_id: str) -> Optional[ScriptModel]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM scripts WHERE project_id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            return None

        cur.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_index ASC", (project_id,))
        scene_rows = cur.fetchall()
        scenes = [
            ScriptScene(
                scene_index=sr["scene_index"],
                narration=sr["narration"],
                duration_est=sr["duration_est"],
                visual_description=sr["visual_description"] or "",
                visual_path=sr["visual_path"],
                transition=sr["transition"] or "fade",
            )
            for sr in scene_rows
        ]

        return ScriptModel(
            hook=row["hook"],
            context=row["context"],
            main_facts=row["main_facts"],
            payoff=row["payoff"],
            cta=row["cta"] or "",
            full_narration=row["full_narration"],
            word_count=row["word_count"],
            estimated_duration_sec=row["estimated_duration"],
            scenes=scenes,
        )


# ==========================================
# Assets Operations
# ==========================================

def save_assets(project_id: str, assets: List[VisualAsset]) -> None:
    with get_db_cursor() as cur:
        for a in assets:
            cur.execute(
                """
                INSERT INTO assets (
                    project_id, asset_id, file_path, source_url, source_name,
                    license, creator, attribution_required, is_procedural
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    a.asset_id,
                    a.file_path,
                    a.source_url,
                    a.source_name,
                    a.license,
                    a.creator,
                    1 if a.attribution_required else 0,
                    1 if a.is_procedural else 0,
                ),
            )


def get_assets(project_id: str) -> List[VisualAsset]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM assets WHERE project_id = ?", (project_id,))
        return [
            VisualAsset(
                asset_id=row["asset_id"],
                file_path=row["file_path"],
                source_url=row["source_url"] or "",
                source_name=row["source_name"] or "",
                license=row["license"] or "Public Domain",
                creator=row["creator"] or "Unknown",
                attribution_required=bool(row["attribution_required"]),
                is_procedural=bool(row["is_procedural"]),
            )
            for row in cur.fetchall()
        ]


# ==========================================
# QC Operations
# ==========================================

def save_qc_result(project_id: str, qc: VideoQCReport) -> None:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO qc_results (
                project_id, passed, quality_score, technical_passed, audio_passed,
                captions_passed, content_passed, issues_json, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                1 if qc.passed else 0,
                qc.quality_score,
                1 if qc.technical_passed else 0,
                1 if qc.audio_passed else 0,
                1 if qc.captions_passed else 0,
                1 if qc.content_passed else 0,
                json.dumps(qc.issues),
                json.dumps(qc.details),
                now,
            ),
        )


def get_latest_qc_result(project_id: str) -> Optional[VideoQCReport]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM qc_results WHERE project_id = ? ORDER BY id DESC LIMIT 1", (project_id,))
        row = cur.fetchone()
        if not row:
            return None
        return VideoQCReport(
            passed=bool(row["passed"]),
            quality_score=row["quality_score"],
            technical_passed=bool(row["technical_passed"]),
            audio_passed=bool(row["audio_passed"]),
            captions_passed=bool(row["captions_passed"]),
            content_passed=bool(row["content_passed"]),
            issues=json.loads(row["issues_json"]),
            details=json.loads(row["details_json"]),
        )


# ==========================================
# Background Jobs Operations
# ==========================================

def create_job(job_id: str, project_id: Optional[str], job_type: str) -> None:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO jobs (id, project_id, job_type, status, error_message, retry_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, project_id, job_type, JobStatus.PENDING.value, None, 0, now, now),
        )


def update_job(job_id: str, status: JobStatus, error_message: Optional[str] = None) -> None:
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            UPDATE jobs 
            SET status = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, error_message, now, job_id),
        )


def list_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]


# ==========================================
# Content Brain Operations
# ==========================================

def seed_default_brain():
    """Seed default characters and baseline category scores."""
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        # Default characters
        cur.execute(
            """
            INSERT OR IGNORE INTO characters (name, persona, visual_style, catchphrase, appearances, created_at)
            VALUES 
            ('Byte', 'Overconfident, hyper-intelligent robot with witty remarks', 'cyan_neon_chibi_robot', 'Calculations never lie, fleshling!', 0, ?),
            ('Sam', 'Grounded, sharp-witted, skeptical human explorer', 'amber_casual_adventurer', 'Wait, hold on a second...', 0, ?)
            """,
            (now, now),
        )

        # Default category scores baseline
        default_cats = [
            ("humor", 89.0),
            ("cartoons", 92.0),
            ("technology", 84.0),
            ("sports", 81.0),
            ("science", 77.0),
            ("news", 68.0),
            ("history", 80.0),
            ("gaming", 82.0),
            ("mystery", 85.0),
            ("space", 88.0),
            ("education", 76.0),
            ("animals", 83.0),
            ("geography", 78.0),
            ("food", 79.0),
            ("entertainment", 82.0),
            ("internet culture", 86.0),
            ("original fiction", 80.0),
        ]
        for cat, initial_score in default_cats:
            cur.execute(
                """
                INSERT OR IGNORE INTO category_scores (category, score, lifetime_videos, avg_quality_score, avg_retention, updated_at)
                VALUES (?, ?, 0, 80.0, 75.0, ?)
                """,
                (cat, initial_score, now),
            )


def get_category_scores() -> List[Dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM category_scores ORDER BY score DESC")
        return [dict(row) for row in cur.fetchall()]


def update_category_score(
    category: str,
    delta: float = 1.0,
    new_quality_score: Optional[float] = None,
    new_retention: Optional[float] = None,
):
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM category_scores WHERE category = ?", (category,))
        row = cur.fetchone()
        if row:
            new_score = max(10.0, min(100.0, row["score"] + delta))
            new_vids = row["lifetime_videos"] + 1
            avg_q = ((row["avg_quality_score"] * row["lifetime_videos"]) + (new_quality_score or 80.0)) / new_vids
            avg_ret = ((row["avg_retention"] * row["lifetime_videos"]) + (new_retention or 70.0)) / new_vids
            cur.execute(
                """
                UPDATE category_scores
                SET score = ?, lifetime_videos = ?, avg_quality_score = ?, avg_retention = ?, updated_at = ?
                WHERE category = ?
                """,
                (new_score, new_vids, avg_q, avg_ret, now, category),
            )
        else:
            cur.execute(
                """
                INSERT INTO category_scores (category, score, lifetime_videos, avg_quality_score, avg_retention, updated_at)
                VALUES (?, 75.0, 1, 80.0, 70.0, ?)
                """,
                (category, now),
            )


def get_characters() -> List[Dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM characters ORDER BY appearances DESC")
        return [dict(row) for row in cur.fetchall()]


def increment_character_appearance(name: str):
    with get_db_cursor() as cur:
        cur.execute("UPDATE characters SET appearances = appearances + 1 WHERE name = ?", (name,))


def save_character(name: str, persona: str, visual_style: str, catchphrase: str = ""):
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT OR REPLACE INTO characters (name, persona, visual_style, catchphrase, appearances, created_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT appearances FROM characters WHERE name = ?), 0), ?)
            """,
            (name, persona, visual_style, catchphrase, name, now),
        )


def get_blacklists(list_type: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db_cursor() as cur:
        if list_type:
            cur.execute("SELECT * FROM blacklists WHERE list_type = ? ORDER BY created_at DESC", (list_type,))
        else:
            cur.execute("SELECT * FROM blacklists ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]


def add_to_blacklist(list_type: str, value: str, reason: str = "") -> bool:
    now = datetime.utcnow().isoformat()
    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                INSERT OR IGNORE INTO blacklists (list_type, value, reason, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (list_type.lower(), value.strip().lower(), reason, now),
            )
        return True
    except Exception:
        return False


def is_blacklisted(text: str, category: Optional[str] = None) -> bool:
    """Check if a topic, word, or category violates human override blacklists."""
    with get_db_cursor() as cur:
        cur.execute("SELECT list_type, value FROM blacklists")
        rows = cur.fetchall()
        lower_text = text.lower()
        lower_cat = (category or "").lower()
        for r in rows:
            val = r["value"]
            if r["list_type"] == "category" and val == lower_cat:
                return True
            if r["list_type"] in ["topic", "keyword"] and val in lower_text:
                return True
    return False


def save_daily_review(review_date: str, successes: str, failures: str, lessons: str, strategy_changes: str):
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT OR REPLACE INTO daily_reviews (review_date, successes, failures, lessons, strategy_changes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (review_date, successes, failures, lessons, strategy_changes, now),
        )


def get_recent_daily_reviews(limit: int = 7) -> List[Dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM daily_reviews ORDER BY review_date DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]


def add_comment_idea(comment_text: str, author: str, derived_topic: Optional[str] = None):
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO comment_ideas (comment_text, author, derived_topic, status, created_at)
            VALUES (?, ?, ?, 'PENDING', ?)
            """,
            (comment_text, author, derived_topic, now),
        )


def get_pending_comment_ideas(limit: int = 20) -> List[Dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM comment_ideas WHERE status = 'PENDING' ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]


def record_analytics(
    project_id: str,
    views: int = 0,
    retention_pct: float = 0.0,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    top_geography: str = "United States",
):
    now = datetime.utcnow().isoformat()
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO analytics_history (project_id, views, retention_pct, likes, comments, shares, top_geography, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, views, retention_pct, likes, comments, shares, top_geography, now),
        )


# Initialize database and seed default brain automatically on import
init_db()
seed_default_brain()
