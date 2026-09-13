from typing import List, Union
from backend.core.config import settings
from backend.core.logging import logger
from backend.models.model_manager import model_manager

class EmbeddingService:
    def __init__(self):
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.model = None

    def _load_model(self):
        if self.model is None:
            if self.provider == "local":
                model_name = model_manager.get_embedding_model()
                logger.info(f"[EmbeddingService] Loading local embedding model: {model_name}")
                from sentence_transformers import SentenceTransformer
                # We load it synchronously here but typically would rely on job queue
                self.model = SentenceTransformer(model_name)
                # Verify dimension
                model_dim = self.model.get_sentence_embedding_dimension()
                if model_dim != self.dimension:
                    logger.warning(f"[EmbeddingService] Config dimension {self.dimension} != model dimension {model_dim}. Updating config to match.")
                    self.dimension = model_dim
                    settings.embedding_dimension = model_dim
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_text(self, text: str) -> List[float]:
        self._load_model()
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        # Enforce batch size dynamically based on hardware
        batch_size = model_manager.get_embedding_batch_size()
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            results.extend(self.model.encode(batch).tolist())
        return results

embedding_service = EmbeddingService()
