"""
Test Script for LTX Video Generation
Verifies text-to-video generation using the LTXVideoService.
"""

import sys
import os

# Add repo root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from backend.services.ltx_service import LTXVideoService

def main():
    print("Initializing LTXVideoService...")
    service = LTXVideoService()

    output_path = "output_test_ltx.mp4"
    prompt = "A breathtaking time-lapse of aurora borealis glowing above a frozen mountain lake"

    print(f"Prompt: {prompt}")
    print("Requesting generation from Lightricks/ltx-video-distilled...")

    result = service.generate_text_to_video(
        prompt=prompt,
        output_path=output_path,
        duration=2
    )

    if result.get("success"):
        file_path = result["video_path"]
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        print("\n=== GENERATION SUCCEEDED ===")
        print(f"Video Path: {file_path}")
        print(f"File Size : {file_size} bytes")
        print(f"Seed Used : {result.get('seed')}")
        print("============================\n")
    else:
        print("\n=== GENERATION FAILED ===")
        print(f"Error: {result.get('error')}")
        print("=========================\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
