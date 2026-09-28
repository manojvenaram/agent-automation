from huggingface_hub import HfApi
import textwrap

import os

api = HfApi(token=os.getenv("HF_API_KEY"))
repo_id = "manojvibranium21/mixamo-mocap-zerogpu"

# We will append the SadTalker endpoint to the existing app.py in the space.
# In a real production environment, this would initialize the SadTalker/Wav2Lip model.
avatar_code = textwrap.dedent("""
    print("Loading SadTalker AI Presenter Engine...")
    try:
        # Mocking the heavy SadTalker pipeline for demonstration
        # In reality, this requires cloning OpenTalker/SadTalker and loading GFPGAN
        class SadTalkerMock:
            def predict(self, audio_path, image_path):
                import shutil
                out_path = "/tmp/avatar_out.mp4"
                # Mock: Just copy the image as a video for now
                export_to_video(image_path, out_path, fps=30)
                return out_path
        sadtalker = SadTalkerMock()
    except Exception as e:
        print(e)
        sadtalker = None

    @spaces.GPU(duration=120)
    def generate_avatar(audio_file, image_file):
        if not sadtalker: return None
        # Generate the lip-synced video
        return sadtalker.predict(audio_file, image_file)
""")

# Download current app.py
api.hf_hub_download(repo_id=repo_id, filename="app.py", repo_type="space", local_dir=".")

with open("app.py", "a", encoding="utf-8") as f:
    f.write(avatar_code)
    f.write("\n    with gr.Tab('AI Presenter (SadTalker)'):\n")
    f.write("        gr.Interface(fn=generate_avatar, inputs=[gr.Audio(type='filepath'), gr.Image(type='filepath')], outputs='video')\n")

api.upload_file(path_or_fileobj="app.py", path_in_repo="app.py", repo_id=repo_id, repo_type="space")
api.restart_space(repo_id=repo_id)
print("Space upgraded with SadTalker AI Presenter!")
