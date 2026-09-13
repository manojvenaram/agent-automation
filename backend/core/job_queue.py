import sqlite3
import time
import json
import uuid
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from backend.core.config import DATA_DIR
from backend.core.logging import logger
from backend.core.resource_manager import resource_manager

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class JobQueue:
    def __init__(self, db_path: Path = DATA_DIR / "job_queue.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    task_type TEXT,
                    payload TEXT,
                    status TEXT,
                    ram_estimate_mb REAL,
                    priority INTEGER,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def enqueue(self, task_id: str, project_id: str, task_type: str, payload: Dict[str, Any], ram_estimate_mb: float = 100.0, priority: int = 1):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jobs (id, project_id, task_type, payload, status, ram_estimate_mb, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, project_id, task_type, json.dumps(payload), TaskStatus.PENDING.value, ram_estimate_mb, priority, time.time()))
            conn.commit()
        logger.info(f"[JobQueue] Enqueued task {task_id} ({task_type}) for project {project_id}")

    def attempt_start_job(self, task_id: str) -> bool:
        """Attempts to transition a specific task to RUNNING if resources allow."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 1. Check if this task is the highest priority pending task that fits in RAM
            cursor = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY priority DESC, created_at ASC", (TaskStatus.PENDING.value,))
            pending_jobs = cursor.fetchall()
            
            for row in pending_jobs:
                if resource_manager.can_allocate(row["ram_estimate_mb"]):
                    # This is the next eligible job
                    if row["id"] == task_id:
                        # It's our job! Start it.
                        conn.execute("UPDATE jobs SET status = ?, started_at = ? WHERE id = ?", 
                                     (TaskStatus.RUNNING.value, time.time(), task_id))
                        conn.commit()
                        return True
                    else:
                        # Another job has priority or fits better, we must wait
                        return False
            return False

    def wait_for_resources(self, project_id: str, task_type: str, ram_estimate_mb: float = 100.0) -> str:
        """Blocks until resources are allocated for this task."""
        task_id = str(uuid.uuid4())
        self.enqueue(task_id, project_id, task_type, {}, ram_estimate_mb)
        
        while not self.attempt_start_job(task_id):
            time.sleep(1.0)
            
        logger.info(f"[JobQueue] Acquired resources for {task_type} (Task {task_id})")
        return task_id

    def complete_job(self, task_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET status = ?, completed_at = ? WHERE id = ?", 
                         (TaskStatus.COMPLETED.value, time.time(), task_id))
            conn.commit()
        logger.info(f"[JobQueue] Completed task {task_id}")

    def fail_job(self, task_id: str, error: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET status = ?, completed_at = ?, error = ?, retry_count = retry_count + 1 WHERE id = ?", 
                         (TaskStatus.FAILED.value, time.time(), error, task_id))
            conn.commit()
        logger.error(f"[JobQueue] Failed task {task_id}: {error}")
        
    def reset_failed(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET status = ? WHERE status = ?", (TaskStatus.PENDING.value, TaskStatus.FAILED.value))
            conn.commit()

job_queue = JobQueue()
