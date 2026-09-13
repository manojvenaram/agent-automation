import numpy as np
import time
import os
import sqlite3
from typing import List, Dict, Any, Tuple
from pathlib import Path
from backend.core.config import settings
from backend.core.logging import logger

class TurboVecMemory:
    """Wrapper around turbovec for local semantic storage."""
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.dimension = settings.embedding_dimension
        self.batch_size = settings.turbovec_batch_size
        self.enabled = settings.turbovec_enabled
        self.index = None
        self.metadata_db_path = index_path.with_name("turbovec_meta.db")
        
        if self.enabled:
            self._init_backend()

    def _init_backend(self):
        import turbovec
        self.index = turbovec.IdMapIndex(self.dimension)
        
        # Load existing index if it exists
        if self.index_path.exists():
            try:
                self.index.load(str(self.index_path))
                logger.info(f"[TurboVecMemory] Loaded existing index with {len(self.index)} vectors.")
            except Exception as e:
                logger.error(f"[TurboVecMemory] Failed to load index: {e}")
        
        # Initialize SQLite for ID mapping
        with sqlite3.connect(self.metadata_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS id_map (
                    int_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    str_id TEXT UNIQUE NOT NULL
                )
            """)
            conn.commit()

    def _get_or_create_int_id(self, str_id: str) -> int:
        with sqlite3.connect(self.metadata_db_path) as conn:
            cursor = conn.execute("SELECT int_id FROM id_map WHERE str_id = ?", (str_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor = conn.execute("INSERT INTO id_map (str_id) VALUES (?)", (str_id,))
            conn.commit()
            return cursor.lastrowid

    def _get_str_id(self, int_id: int) -> str:
        with sqlite3.connect(self.metadata_db_path) as conn:
            cursor = conn.execute("SELECT str_id FROM id_map WHERE int_id = ?", (int_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def add_vectors(self, str_ids: List[str], vectors: List[List[float]]):
        if not self.enabled or not vectors:
            return

        int_ids = [self._get_or_create_int_id(sid) for sid in str_ids]
        np_vectors = np.array(vectors, dtype=np.float32)
        np_ids = np.array(int_ids, dtype=np.uint64)

        try:
            self.index.add_with_ids(np_vectors, np_ids)
            if settings.turbovec_autosave:
                self.index.write(str(self.index_path))
        except Exception as e:
            logger.error(f"[TurboVecMemory] Error adding vectors: {e}")

    def search(self, query_vector: List[float], k: int = 10) -> List[Tuple[str, float]]:
        if not self.enabled or len(self.index) == 0:
            return []

        try:
            np_query = np.array([query_vector], dtype=np.float32)
            distances, res_ids = self.index.search(np_query, k)
            
            results = []
            for i in range(len(res_ids[0])):
                int_id = int(res_ids[0][i])
                dist = float(distances[0][i])
                if int_id != 0: # 0 can be empty slot in some vector DBs depending on implementation, but let's check str_id
                    str_id = self._get_str_id(int_id)
                    if str_id:
                        results.append((str_id, dist))
            return results
        except Exception as e:
            logger.error(f"[TurboVecMemory] Search error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled"}
        
        return {
            "status": "active",
            "total_vectors": len(self.index) if self.index else 0,
            "dimension": self.dimension,
            "index_path": str(self.index_path)
        }

turbovec_memory = TurboVecMemory(settings.turbovec_index_path)
