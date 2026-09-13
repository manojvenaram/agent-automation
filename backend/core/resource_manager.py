import psutil
import platform
import os
import pynvml
from typing import Dict, Any
from backend.core.logging import logger

class ResourceManager:
    def __init__(self):
        self.total_ram_mb = psutil.virtual_memory().total / (1024 * 1024)
        self.cpu_cores = psutil.cpu_count(logical=False) or 1
        self.logical_cores = psutil.cpu_count(logical=True) or 1
        self.system = platform.system()
        
        self.gpu_available = False
        self.gpu_name = "None"
        self.gpu_vram_mb = 0.0
        self._init_nvml()
        
        self._detect_profile()
        logger.info(f"[ResourceManager] Initialized profile: {self.profile_name} (RAM: {self.total_ram_mb:.0f}MB, VRAM: {self.gpu_vram_mb:.0f}MB)")

    def _init_nvml(self):
        try:
            pynvml.nvmlInit()
            deviceCount = pynvml.nvmlDeviceGetCount()
            if deviceCount > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self.gpu_name = pynvml.nvmlDeviceGetName(handle)
                meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
                self.gpu_vram_mb = meminfo.total / (1024 * 1024)
                self.gpu_available = True
        except Exception as e:
            logger.warning(f"[ResourceManager] GPU detection failed or no NVIDIA GPU: {e}")

    def _detect_profile(self):
        if self.total_ram_mb <= 6000 or (self.gpu_available and self.gpu_vram_mb <= 2048):
            self.profile_name = "LOW"
            self.max_concurrent_tasks = 1
            self.embedding_batch_size = 2
            self.render_mode = "low_resource"
        elif self.total_ram_mb <= 12000 or (self.gpu_available and self.gpu_vram_mb <= 6000):
            self.profile_name = "BALANCED"
            self.max_concurrent_tasks = 1
            self.embedding_batch_size = 8
            self.render_mode = "standard"
        else:
            self.profile_name = "PERFORMANCE"
            self.max_concurrent_tasks = 2
            self.embedding_batch_size = 16
            self.render_mode = "standard"

    def get_hardware_profile(self) -> Dict[str, Any]:
        return {
            "profile": self.profile_name,
            "total_ram_mb": self.total_ram_mb,
            "cpu_cores": self.cpu_cores,
            "logical_cores": self.logical_cores,
            "os": self.system,
            "gpu_available": self.gpu_available,
            "gpu_name": self.gpu_name,
            "gpu_vram_mb": self.gpu_vram_mb
        }

    def get_current_usage(self) -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        usage = {
            "ram_used_percent": mem.percent,
            "ram_available_mb": mem.available / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "vram_used_percent": 0.0,
            "vram_available_mb": 0.0
        }
        
        if self.gpu_available:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
                usage["vram_used_percent"] = (meminfo.used / meminfo.total) * 100.0
                usage["vram_available_mb"] = meminfo.free / (1024 * 1024)
            except Exception:
                pass
                
        return usage

    def is_emergency_mode(self) -> bool:
        usage = self.get_current_usage()
        if usage["ram_used_percent"] > 90.0:
            return True
        if self.gpu_available and usage["vram_used_percent"] > 90.0:
            return True
        return False

    def can_allocate(self, estimated_ram_mb: float) -> bool:
        if self.is_emergency_mode():
            return False
            
        available_mb = psutil.virtual_memory().available / (1024 * 1024)
        if available_mb - estimated_ram_mb < 500:
            return False
        return True

resource_manager = ResourceManager()
