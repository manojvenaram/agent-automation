from typing import Optional
from backend.core.logging import logger
from backend.core.config import settings
from backend.core.resource_manager import resource_manager

class ModelManager:
    """Intelligently selects and degrades ML models based on available hardware."""
    
    def __init__(self):
        self.preferred_llm = settings.ollama_model
        self.preferred_embedding = settings.embedding_model
        self.preferred_whisper = "base" # default, could be moved to config
        
    def get_llm_model(self) -> str:
        """Returns the appropriate LLM model name, falling back to smaller quantized versions if RAM is low."""
        if resource_manager.is_emergency_mode():
            logger.warning("[ModelManager] Emergency mode: Downgrading LLM to tiny quantized model.")
            return "qwen2.5:0.5b" # extremely small model
            
        profile = resource_manager.get_hardware_profile()["profile"]
        if profile == "LOW":
            return "qwen2.5:1.5b" # small footprint
            
        return self.preferred_llm

    def get_embedding_model(self) -> str:
        """Returns the embedding model. In emergency mode, could return a smaller dimension model."""
        if resource_manager.is_emergency_mode():
            logger.warning("[ModelManager] Emergency mode: Downgrading Embedding Model.")
            return "paraphrase-MiniLM-L3-v2" # smaller than L6
            
        return self.preferred_embedding
        
    def get_whisper_model(self) -> str:
        if resource_manager.is_emergency_mode():
            logger.warning("[ModelManager] Emergency mode: Downgrading Whisper to tiny.")
            return "tiny"
            
        profile = resource_manager.get_hardware_profile()["profile"]
        if profile == "LOW":
            return "tiny"
        elif profile == "BALANCED":
            return "tiny" # For 8GB RAM, tiny is much safer
        return self.preferred_whisper
        
    def get_embedding_batch_size(self) -> int:
        if resource_manager.is_emergency_mode():
            return 1
            
        profile = resource_manager.get_hardware_profile()["profile"]
        if profile == "LOW":
            return 2
        elif profile == "BALANCED":
            return 4
        return settings.embedding_batch_size

model_manager = ModelManager()
