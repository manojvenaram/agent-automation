import sys
from backend.agents.orchestrator import MultiAgentOrchestrator
from backend.core.logging import logger
import logging

# Ensure we can see the logs in the console
logging.basicConfig(level=logging.INFO)

def main():
    print("Initializing Orchestrator...")
    orchestrator = MultiAgentOrchestrator()
    
    print("\nStarting the Agent Workflow (This might take a few moments for TTS & Video Rendering)...")
    
    # Run the workflow
    result = orchestrator.run_workflow(
        topic="How Neural Networks Learn",
        category="Technology",
        video_format="DID_YOU_KNOW"
    )
    
    print("\n" + "="*50)
    print("WORKFLOW COMPLETE!")
    print("="*50)
    print(f"\nFinal Video saved to: {result.get('final_video_path')}")
    print("\nGenerated Script:")
    print("-" * 20)
    print(result.get('script'))
    print("-" * 20)
    
if __name__ == "__main__":
    main()
