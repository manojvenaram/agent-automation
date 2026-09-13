"""
Background Job Queue Manager for YouTube Shorts Agent.
Runs generation tasks asynchronously in worker threads and logs progress to DB.
"""

import threading
import uuid
from typing import Any, Callable, Dict, Optional
from backend.core.database import create_job, update_job
from backend.core.logging import logger
from backend.core.orchestrator import orchestrator
from backend.models import JobStatus


class JobQueueManager:
    def __init__(self):
        self._active_threads: Dict[str, threading.Thread] = {}

    def submit_generation_job(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        auto_publish: Optional[bool] = None,
    ) -> str:
        """Enqueue an asynchronous pipeline generation task."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        logger.info(f"Submitting new generation job: {job_id}")

        create_job(job_id=job_id, project_id=None, job_type="GENERATE_SHORT")

        def _worker():
            try:
                update_job(job_id, JobStatus.RUNNING)
                project = orchestrator.run_pipeline(
                    topic_input=topic,
                    category=category,
                    auto_publish=auto_publish,
                )
                if project.state.value in ["QC_PASSED", "APPROVED", "PUBLISHED"]:
                    update_job(job_id, JobStatus.COMPLETED)
                else:
                    update_job(job_id, JobStatus.FAILED, error_message=project.error_message)
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
                update_job(job_id, JobStatus.FAILED, error_message=str(e))
            finally:
                self._active_threads.pop(job_id, None)

        thread = threading.Thread(target=_worker, daemon=True)
        self._active_threads[job_id] = thread
        thread.start()

        return job_id


# Global singleton instance
job_manager = JobQueueManager()
