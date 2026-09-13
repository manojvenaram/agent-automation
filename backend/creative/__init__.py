"""
Creative Engine package for YouTube Shorts Intelligence Agent.
Handles Creative Direction, Narrative Architectures, Hook Generation & Optimization,
Viewer Simulation, and Procedural Cartoon Generation.
"""

from .creative_director import CreativeDirectorAgent, CreativeDirection, ShortsFormat, VisualTreatment
from .story_engine import StoryEngine, StoryStructure, StoryBeat
from .hook_lab import HookLab, CandidateHook
from .viewer_simulator import ViewerSimulatorAgent, SimulationResult, ViewerPersona
from .cartoon_engine import CartoonEngine, CharacterPose

__all__ = [
    "CreativeDirectorAgent",
    "CreativeDirection",
    "ShortsFormat",
    "VisualTreatment",
    "StoryEngine",
    "StoryStructure",
    "StoryBeat",
    "HookLab",
    "CandidateHook",
    "ViewerSimulatorAgent",
    "SimulationResult",
    "ViewerPersona",
    "CartoonEngine",
    "CharacterPose",
]
