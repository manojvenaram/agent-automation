import os
import shutil
from pathlib import Path
from backend.core.config import settings, ASSETS_DIR, LOGS_DIR
from backend.core.logging import logger

class CacheManager:
    def __init__(self):
        self.max_bytes = settings.cache_max_gb * 1024 * 1024 * 1024
        
        # Directories that can be cleared safely (intermediate renders, temporary audio)
        self.cache_dirs = [
            ASSETS_DIR / "temp",
            ASSETS_DIR / "audio_cache",
            ASSETS_DIR / "video_cache",
            LOGS_DIR
        ]
        
        for d in self.cache_dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _get_dir_size(self, path: Path) -> int:
        total = 0
        if not path.exists():
            return 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
        return total

    def _get_all_cache_files(self) -> list:
        files = []
        for d in self.cache_dirs:
            if not d.exists():
                continue
            for dirpath, _, filenames in os.walk(d):
                for f in filenames:
                    fp = Path(os.path.join(dirpath, f))
                    # Protect vital DB files just in case
                    if fp.suffix in [".sqlite", ".tvec", ".json"]:
                        continue
                    files.append({
                        "path": fp,
                        "size": fp.stat().st_size,
                        "mtime": fp.stat().st_mtime
                    })
        return files

    def enforce_limits(self):
        total_size = sum(self._get_dir_size(d) for d in self.cache_dirs)
        
        if total_size <= self.max_bytes:
            return
            
        logger.warning(f"[CacheManager] Cache size ({total_size / (1024*1024):.1f} MB) exceeds {settings.cache_max_gb} GB limit. Purging...")
        
        files = self._get_all_cache_files()
        # Sort files by modification time (oldest first)
        files.sort(key=lambda x: x["mtime"])
        
        freed = 0
        for f in files:
            if total_size - freed <= self.max_bytes:
                break
            try:
                os.remove(f["path"])
                freed += f["size"]
                logger.debug(f"[CacheManager] Evicted {f['path'].name}")
            except Exception as e:
                logger.error(f"[CacheManager] Failed to remove {f['path']}: {e}")
                
        logger.info(f"[CacheManager] Eviction complete. Freed {freed / (1024*1024):.1f} MB.")

cache_manager = CacheManager()
