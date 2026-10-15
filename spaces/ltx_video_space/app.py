import os
import shutil
import gradio as gr
from gradio_client import Client, handle_file

print("Initializing LTX Video Studio...")

LTX_DISTILLED_SPACE = "Lightricks/ltx-video-distilled"
LTX_25_SPACE = "Lightricks/LTX-2.5"

_distilled_client = None
_ltx25_client = None

def get_distilled_client():
    global _distilled_client
    if _distilled_client is None:
        _distilled_client = Client(LTX_DISTILLED_SPACE)
    return _distilled_client

def get_ltx25_client():
    global _ltx25_client
    if _ltx25_client is None:
        _ltx25_client = Client(LTX_25_SPACE)
    return _ltx25_client

def generate_t2v(prompt, negative_prompt, duration, width, height, seed, randomize_seed):
    try:
        client = get_distilled_client()
        result = client.predict(
            prompt=prompt,
            negative_prompt=negative_prompt or "worst quality, blurry, jittery, distorted",
            input_image_filepath=None,
            input_video_filepath=None,
            height_ui=float(height),
            width_ui=float(width),
            mode="text-to-video",
            duration_ui=float(duration),
            ui_frames_to_use=9,
            seed_ui=int(seed),
            randomize_seed=randomize_seed,
            ui_guidance_scale=1.0,
            improve_texture_flag=True,
            api_name="/text_to_video"
        )
        video_path = result[0]["video"] if isinstance(result[0], dict) else result[0]
        used_seed = result[1] if len(result) > 1 else seed
        return video_path, f"Generated with seed: {used_seed}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def generate_i2v(image, prompt, negative_prompt, duration, seed, randomize_seed):
    if image is None:
        return None, "Please upload an input image."
    try:
        client = get_distilled_client()
        result = client.predict(
            prompt=prompt or "Make this image come alive with cinematic motion, smooth animation",
            negative_prompt=negative_prompt or "worst quality, blurry, distorted",
            input_image_filepath=handle_file(image),
            input_video_filepath=None,
            height_ui=512.0,
            width_ui=704.0,
            mode="image-to-video",
            duration_ui=float(duration),
            ui_frames_to_use=9,
            seed_ui=int(seed),
            randomize_seed=randomize_seed,
            ui_guidance_scale=1.0,
            improve_texture_flag=True,
            api_name="/image_to_video"
        )
        video_path = result[0]["video"] if isinstance(result[0], dict) else result[0]
        used_seed = result[1] if len(result) > 1 else seed
        return video_path, f"Generated with seed: {used_seed}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def generate_audiovideo_25(prompt, image, duration, decoder, do_enhance):
    try:
        client = get_ltx25_client()
        img_param = handle_file(image) if image else None
        result = client.predict(
            prompt=prompt,
            image_path=img_param,
            height=768.0,
            width=512.0,
            duration_s=float(duration),
            seed=42.0,
            decoder=decoder,
            auto_len=False,
            randomize_seed=True,
            do_enhance=do_enhance,
            api_name="/run"
        )
        video_with_audio = result[0]
        enhanced_prompt = result[1] if len(result) > 1 else prompt
        return video_with_audio, f"Enhanced Prompt: {enhanced_prompt}"
    except Exception as e:
        return None, f"Error: {str(e)}"

# Custom CSS for modern styling
custom_css = """
.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
}
.header-box {
    text-align: center;
    padding: 24px 0 16px 0;
}
.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.header-subtitle {
    font-size: 1.05rem;
    color: #6b7280;
}
"""

with gr.Blocks(css=custom_css, title="LTX Video Studio") as demo:
    gr.HTML("""
    <div class="header-box">
        <div class="header-title">🎬 LTX Video Studio</div>
        <div class="header-subtitle">Powered by Lightricks LTX Foundation Models (Zero GPU Overhead)</div>
    </div>
    """)

    with gr.Tabs():
        # TAB 1: Text-to-Video
        with gr.TabItem("✨ Text-to-Video"):
            with gr.Row():
                with gr.Column(scale=5):
                    t2v_prompt = gr.Textbox(
                        label="Prompt",
                        placeholder="Cinematic drone shot flying through a glowing cyberpunk city in the rain, hyperrealistic 4k...",
                        lines=3
                    )
                    t2v_neg = gr.Textbox(
                        label="Negative Prompt",
                        value="worst quality, inconsistent motion, blurry, jittery, distorted",
                        lines=1
                    )
                    with gr.Row():
                        t2v_duration = gr.Slider(minimum=2, maximum=5, step=1, value=2, label="Duration (seconds)")
                        t2v_width = gr.Slider(minimum=384, maximum=1024, step=64, value=704, label="Width")
                        t2v_height = gr.Slider(minimum=256, maximum=768, step=64, value=512, label="Height")
                    with gr.Row():
                        t2v_seed = gr.Number(value=42, label="Seed", precision=0)
                        t2v_rand = gr.Checkbox(value=True, label="Randomize Seed")
                    
                    t2v_btn = gr.Button("Generate Video", variant="primary", size="lg")

                with gr.Column(scale=5):
                    t2v_output = gr.Video(label="Generated Video", interactive=False)
                    t2v_status = gr.Textbox(label="Status", interactive=False)

            t2v_btn.click(
                fn=generate_t2v,
                inputs=[t2v_prompt, t2v_neg, t2v_duration, t2v_width, t2v_height, t2v_seed, t2v_rand],
                outputs=[t2v_output, t2v_status]
            )

        # TAB 2: Image-to-Video
        with gr.TabItem("🖼️ Image-to-Video"):
            with gr.Row():
                with gr.Column(scale=5):
                    i2v_image = gr.Image(type="filepath", label="Input Image")
                    i2v_prompt = gr.Textbox(
                        label="Motion Prompt",
                        value="Make this image come alive with cinematic motion, smooth animation",
                        lines=2
                    )
                    i2v_neg = gr.Textbox(
                        label="Negative Prompt",
                        value="worst quality, inconsistent motion, blurry, jittery, distorted",
                        lines=1
                    )
                    with gr.Row():
                        i2v_duration = gr.Slider(minimum=2, maximum=4, step=1, value=2, label="Duration (seconds)")
                        i2v_seed = gr.Number(value=42, label="Seed", precision=0)
                        i2v_rand = gr.Checkbox(value=True, label="Randomize Seed")
                    
                    i2v_btn = gr.Button("Animate Image", variant="primary", size="lg")

                with gr.Column(scale=5):
                    i2v_output = gr.Video(label="Animated Video", interactive=False)
                    i2v_status = gr.Textbox(label="Status", interactive=False)

            i2v_btn.click(
                fn=generate_i2v,
                inputs=[i2v_image, i2v_prompt, i2v_neg, i2v_duration, i2v_seed, i2v_rand],
                outputs=[i2v_output, i2v_status]
            )

        # TAB 3: LTX-2.5 Audio + Video
        with gr.TabItem("🔊 LTX-2.5 (Video + Audio)"):
            with gr.Row():
                with gr.Column(scale=5):
                    av_prompt = gr.Textbox(
                        label="Audio-Visual Prompt",
                        placeholder="Ocean waves crashing powerfully against dark rocky cliffs at sunset, realistic roaring sound of water...",
                        lines=3
                    )
                    av_image = gr.Image(type="filepath", label="Optional Starting Frame")
                    with gr.Row():
                        av_duration = gr.Slider(minimum=1.5, maximum=4.0, step=0.5, value=2.0, label="Duration (s)")
                        av_decoder = gr.Radio(choices=["conv", "diffusion"], value="conv", label="Decoder")
                    av_enhance = gr.Checkbox(value=True, label="Auto-Enhance Prompt")

                    av_btn = gr.Button("Generate Synchronized Video + Audio", variant="primary", size="lg")

                with gr.Column(scale=5):
                    av_output = gr.Video(label="Generated Video (with Audio)", interactive=False)
                    av_status = gr.Textbox(label="Status / Enhanced Prompt", interactive=False)

            av_btn.click(
                fn=generate_audiovideo_25,
                inputs=[av_prompt, av_image, av_duration, av_decoder, av_enhance],
                outputs=[av_output, av_status]
            )

    gr.Markdown("--- \nBuilt with ❤️ using Lightricks LTX and Hugging Face.")

if __name__ == "__main__":
    demo.queue().launch()
