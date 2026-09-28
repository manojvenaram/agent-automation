from huggingface_hub import HfApi

import os
api = HfApi(token=os.getenv("HF_API_KEY"))
repo_id = "manojvibranium21/mixamo-mocap-zerogpu"

app_py_content = """import spaces
import gradio as gr
import torch
import scipy.io.wavfile
import numpy as np
from transformers import pipeline, AutoProcessor, MusicgenForConditionalGeneration
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video

print("Loading Whisper-v3-Turbo...")
try:
    pipe_whisper = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", torch_dtype=torch.float16, device="cuda")
except Exception: pipe_whisper = None

print("Loading MusicGen...")
try:
    processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model_music = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small").to("cuda")
except Exception: processor = model_music = None

print("Loading Text-to-Video Engine (Zeroscope)...")
try:
    pipe_video = DiffusionPipeline.from_pretrained("damo-vilab/text-to-video-ms-1.7b", torch_dtype=torch.float16, variant="fp16")
    pipe_video.scheduler = DPMSolverMultistepScheduler.from_config(pipe_video.scheduler.config)
    pipe_video.enable_model_cpu_offload()
except Exception as e: 
    print(e)
    pipe_video = None


@spaces.GPU
def generate_captions(audio_file):
    if not pipe_whisper: return {}
    return pipe_whisper(audio_file, chunk_length_s=30, batch_size=24, return_timestamps="word")

@spaces.GPU
def generate_music(prompt, duration_sec):
    if not model_music: return None
    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to("cuda")
    max_new_tokens = int(float(duration_sec) * 51.2)
    audio_values = model_music.generate(**inputs, max_new_tokens=max_new_tokens)
    out_path = "/tmp/musicgen_out.wav"
    scipy.io.wavfile.write(out_path, rate=model_music.config.audio_encoder.sampling_rate, data=audio_values[0, 0].cpu().numpy())
    return out_path

@spaces.GPU(duration=120)
def generate_broll(prompt):
    if not pipe_video: return None
    # Add cinematic keywords automatically
    full_prompt = f"highly detailed, 4k resolution, beautiful cinematic shot, {prompt}, masterpiece, trending on artstation"
    video_frames = pipe_video(full_prompt, num_inference_steps=25, num_frames=32).frames[0]
    out_path = "/tmp/broll_out.mp4"
    export_to_video(video_frames, out_path, fps=8)
    return out_path


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Universal Agent ZeroGPU Backend")
    with gr.Tab("Whisper-v3 Captions"):
        gr.Interface(fn=generate_captions, inputs=gr.Audio(type="filepath"), outputs="json")
    with gr.Tab("Meta MusicGen"):
        gr.Interface(fn=generate_music, inputs=["text", "slider"], outputs="audio")
    with gr.Tab("AI B-Roll (Text-to-Video)"):
        gr.Interface(fn=generate_broll, inputs=gr.Textbox(label="Video Prompt"), outputs="video")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
"""

req_txt = """gradio>=4.0.0
torch
transformers
accelerate
librosa
soundfile
scipy
diffusers
opencv-python
imageio
imageio-ffmpeg
"""

with open("app.py", "w", encoding="utf-8") as f: f.write(app_py_content)
with open("requirements.txt", "w", encoding="utf-8") as f: f.write(req_txt)

api.upload_file(path_or_fileobj="app.py", path_in_repo="app.py", repo_id=repo_id, repo_type="space")
api.upload_file(path_or_fileobj="requirements.txt", path_in_repo="requirements.txt", repo_id=repo_id, repo_type="space")
api.restart_space(repo_id=repo_id)
print("Space upgraded with Text-to-Video AI B-Roll!")
