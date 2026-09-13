import uuid
import time
from typing import Dict, Any, List, Optional
from backend.core.logging import logger
from backend.memory.embedding_service import embedding_service
from backend.memory.turbovec_memory import turbovec_memory
from backend.core.database import DB_PATH
import sqlite3

class MemoryManager:
    """Orchestrates structured (SQLite) and semantic (TurboVec) memory."""

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_records (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL
                )
            """)
            conn.commit()

    def store_memory(self, memory_type: str, content: str, metadata: Dict[str, Any] = None):
        """Stores a piece of knowledge structurally and semantically."""
        mem_id = str(uuid.uuid4())
        
        # 1. Generate Embedding
        vector = embedding_service.embed_text(content)
        
        # 2. Store in TurboVec
        turbovec_memory.add_vectors([mem_id], [vector])
        
        # 3. Store Structured Record in SQLite
        import json
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO semantic_records (id, type, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (mem_id, memory_type, content, json.dumps(metadata or {}), time.time()))
            conn.commit()
            
        logger.info(f"[MemoryManager] Stored '{memory_type}' memory (ID: {mem_id})")

    def search_similar(self, query: str, k: int = 5, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Retrieves semantically similar memories."""
        query_vector = embedding_service.embed_text(query)
        results = turbovec_memory.search(query_vector, k=k)
        
        memories = []
        import json
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            for str_id, dist in results:
                # Assuming lower distance = more similar in TurboVec (L2 or Cosine distance)
                if dist > threshold: 
                    continue
                    
                cursor = conn.execute("SELECT * FROM semantic_records WHERE id = ?", (str_id,))
                row = cursor.fetchone()
                if row:
                    mem = dict(row)
                    mem["metadata"] = json.loads(mem["metadata"])
                    mem["distance"] = dist
                    memories.append(mem)
                    
        return memories

    def check_duplication(self, text: str, threshold: float = 0.2) -> bool:
        """Checks if a similar concept already exists."""
        similar = self.search_similar(text, k=1, threshold=threshold)
        if similar:
            logger.warning(f"[MemoryManager] Duplication detected (Dist: {similar[0]['distance']:.3f})")
            return True
        return False

    def get_stats(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM semantic_records")
            sqlite_count = cursor.fetchone()[0]
            
        tv_stats = turbovec_memory.get_stats()
        return {
            "structured_records": sqlite_count,
            "semantic_vectors": tv_stats.get("total_vectors", 0),
            "turbovec_status": tv_stats.get("status")
        }


memory_manager = MemoryManager()
