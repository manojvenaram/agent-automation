"""
Deploy LTX Video Studio to Hugging Face Spaces.
"""

import os
import sys
from dotenv import load_dotenv
from huggingface_hub import HfApi

load_dotenv()

HF_TOKEN = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("Error: HF_API_KEY or HF_TOKEN not found in environment!")
    sys.exit(1)

api = HfApi(token=HF_TOKEN)
user = api.whoami()
username = user["name"]

# Target space: defaulting to existing ChatGPT4 space or CLI argument
target_repo = sys.argv[1] if len(sys.argv) > 1 else "ChatGPT4"
REPO_ID = f"{username}/{target_repo}"
SPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "spaces", "ltx_video_space"))

print(f"Deploying LTX Video Studio to Hugging Face Space: {REPO_ID} ...")

try:
    files_to_upload = ["app.py", "requirements.txt", "README.md"]
    for filename in files_to_upload:
        file_path = os.path.join(SPACE_DIR, filename)
        if os.path.exists(file_path):
            print(f"Uploading {filename} to {REPO_ID}...")
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=filename,
                repo_id=REPO_ID,
                repo_type="space"
            )

    print("Triggering space restart...")
    api.restart_space(repo_id=REPO_ID)

    print("\n=== DEPLOYMENT SUCCESSFUL ===")
    print(f"Your Hugging Face Space is live at:")
    print(f"URL: https://huggingface.co/spaces/{REPO_ID}")
    print("===============================\n")

except Exception as e:
    print(f"Deployment error: {e}")
    sys.exit(1)
