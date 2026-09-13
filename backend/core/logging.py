"""
Structured Logger for YouTube Shorts Agent.
Outputs formatted logs to console and rotates project-specific and global log files.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from backend.core.config import LOGS_DIR

# Global app logger
logger = logging.getLogger("ShortsAgent")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers
if not logger.handlers:
    # Console formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Master file logging
    master_log_file = LOGS_DIR / f"agent_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(master_log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def get_project_logger(project_id: str, project_dir: Path) -> logging.Logger:
    """Return a logger configured to write to the project's specific log directory."""
    proj_logger = logging.getLogger(f"ShortsAgent.{project_id}")
    proj_logger.setLevel(logging.INFO)
    
    # Check if this logger already has project file handler
    project_log_file = project_dir / "logs" / "execution.log"
    project_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    handler_exists = any(
        isinstance(h, logging.FileHandler) and Path(h.baseFilename) == project_log_file 
        for h in proj_logger.handlers
    )
    
    if not handler_exists:
        fh = logging.FileHandler(project_log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
        proj_logger.addHandler(fh)
        
    return proj_logger
