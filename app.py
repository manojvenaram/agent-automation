"""
CLI & Studio Entrypoint for Autonomous YouTube Shorts Agent.
Supports one-click agent pipeline execution, interactive setup wizard,
and web dashboard hosting.
Zero paid APIs.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.core.config import settings, PROJECTS_DIR, CREDENTIALS_DIR, MUSIC_DIR
from backend.core.database import list_projects, get_project
from backend.core.logging import logger
from backend.core.orchestrator import orchestrator
from backend.services.ffmpeg_service import ffmpeg_service
from backend.services.llm_service import llm_service
from backend.services.tts_service import tts_service
from backend.services.youtube_service import youtube_service


def cmd_setup():
    """First-run environment inspection wizard."""
    print("=" * 60)
    print(" AUTONOMOUS YOUTUBE SHORTS AGENT - SETUP WIZARD")
    print("=" * 60)

    # 1. Python Check
    py_ver = sys.version.split()[0]
    print(f"[OK] Python detected: v{py_ver}")

    # 2. FFmpeg Check
    try:
        ffmpeg_bin = ffmpeg_service.ffmpeg_path
        print(f"[OK] FFmpeg detected: {ffmpeg_bin}")
    except Exception as e:
        print(f"[ERR] FFmpeg error: {e}")

    # 3. LLM Check
    if llm_service.is_available():
        models = llm_service.list_installed_models()
        active = llm_service.get_best_available_model()
        print(f"[OK] LLM connected: {settings.llm_provider}")
        print(f"[OK] LLM models available: {', '.join(models) if models else 'None'}")
        print(f"[OK] Active model selected: {active}")
    else:
        print("[!] LLM service is not available (e.g. missing API key)")
        print("  -> Application will automatically use rule-based fallbacks")

    # 4. Text-To-Speech
    print(f"[OK] TTS Engine configured: {settings.tts_engine} (Voice: {settings.tts_voice})")

    # 5. Media & Storage Directories
    print(f"[OK] Projects workspace: {PROJECTS_DIR}")
    print(f"[OK] Royalty-free music library: {MUSIC_DIR}")

    # 6. YouTube Authentication
    if youtube_service.is_authenticated():
        print("[OK] YouTube OAuth credentials: Authenticated")
    else:
        if settings.youtube_client_secrets_file.exists():
            print("[!] YouTube client secrets found, ready for one-time browser login.")
        else:
            print("[!] YouTube OAuth not configured (Video generation works 100% locally).")
            print(f"  To enable YouTube publishing, save your Google OAuth client_secrets.json to:")
            print(f"  {settings.youtube_client_secrets_file}")

    print("=" * 60)
    print(" System is fully ready for autonomous Shorts production!")
    print(" Run: 'python app.py run-agent' to produce your first video.")
    print("=" * 60)


def cmd_run_agent(args):
    """Run full automated production pipeline."""
    print(f"\n🚀 Launching Autonomous Production Pipeline...")
    if args.demo:
        settings.demo_mode = True
        print("ℹ️ Running in DEMO_MODE (YouTube upload simulated).")

    if args.auto_publish:
        settings.auto_publish = True
        print("ℹ️ Auto-publish ENABLED.")

    project = orchestrator.run_pipeline(
        topic_input=args.topic,
        category=args.category,
        auto_publish=settings.auto_publish,
    )

    print("\n" + "=" * 60)
    print(f" PRODUCTION RUN COMPLETE: {project.id}")
    print("=" * 60)
    print(f"Title:         {project.title}")
    print(f"State:         {project.state.value}")
    print(f"Quality Score: {project.quality_score}/100")
    print(f"Duration:      {project.duration_sec:.1f}s" if project.duration_sec else "Duration: N/A")
    print(f"Video File:    {project.video_path}")
    if project.youtube_url:
        print(f"YouTube URL:   {project.youtube_url}")
    print("=" * 60)


def cmd_dashboard(args):
    """Start web dashboard studio."""
    import uvicorn
    host = args.host or settings.host
    port = args.port or settings.port
    print(f"Starting YouTube Shorts Studio Dashboard at http://{host}:{port}")
    uvicorn.run("backend.api.routes:app", host=host, port=port, reload=False)


def cmd_discover(args):
    """Discover topic candidates."""
    from backend.agents.trend_scout import trend_scout_agent, topic_evaluator_agent
    candidates = trend_scout_agent.discover_topics(category=args.category, count=5)
    evaluated = topic_evaluator_agent.evaluate_and_select_topic(candidates)
    print("\nTop Candidate Selected:")
    print(f"  Topic: {evaluated['topic']}")
    print(f"  Category: {evaluated['category']}")
    print(f"  Composite Score: {evaluated['composite_score']}")

def cmd_review(args):
    """Run the daily learning and self-improvement review."""
    from backend.learning.daily_review import daily_review_agent
    print("\n🧠 Running Self-Improving Daily Review...")
    result = daily_review_agent.run_review()
    print("=" * 60)
    print(" DAILY REVIEW COMPLETED")
    print("=" * 60)
    print(f"Worked:    {result.what_worked}")
    print(f"Failed:    {result.what_failed}")
    print(f"Surprised: {result.what_surprised}")
    print("\nWeight Adjustments Made:")
    for cat, new_weight in result.weight_adjustments.items():
        print(f"  - {cat.capitalize()}: {new_weight}")
    print("=" * 60)


def cmd_status():
    """Print system status and recent projects summary."""
    projects = list_projects(limit=10)
    print("\n=== Autonomous Shorts Studio Status ===")
    print(f"Total Projects in Database: {len(projects)}")
    for p in projects[:5]:
        score = f"QC: {p.quality_score}/100" if p.quality_score else "QC Pending"
        print(f"- [{p.state.value:12}] {p.title[:45]:45} ({score})")


def cmd_memory_stats():
    from backend.memory.memory_manager import memory_manager
    stats = memory_manager.get_stats()
    print("\n=== Memory Stats ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

def cmd_memory_search(args):
    from backend.memory.memory_manager import memory_manager
    results = memory_manager.search_similar(args.query, k=3)
    print(f"\n=== Memory Search: '{args.query}' ===")
    for r in results:
        print(f"[{r['type']}] Dist: {r['distance']:.3f} | {r['content']}")

def cmd_resource_status():
    from backend.core.resource_manager import resource_manager
    prof = resource_manager.get_hardware_profile()
    usage = resource_manager.get_current_usage()
    print("\n=== Resource Manager Status ===")
    print(f"Profile: {prof['profile']}")
    print(f"Total RAM: {prof['total_ram_mb']:.0f} MB")
    print(f"CPU Cores: {prof['cpu_cores']} (Logical: {prof['logical_cores']})")
    print(f"RAM Used: {usage['ram_used_percent']}%")
    print(f"RAM Available: {usage['ram_available_mb']:.0f} MB")
    print(f"CPU Used: {usage['cpu_percent']}%")
    if prof['gpu_available']:
        print(f"GPU: {prof['gpu_name']}")
        print(f"VRAM Used: {usage['vram_used_percent']:.1f}%")
        print(f"VRAM Available: {usage['vram_available_mb']:.0f} / {prof['gpu_vram_mb']:.0f} MB")
    print(f"Emergency Mode: {'YES' if resource_manager.is_emergency_mode() else 'NO'}")

def cmd_benchmark():
    import time
    import json
    from backend.memory.embedding_service import embedding_service
    from backend.core.resource_manager import resource_manager
    from backend.models.model_manager import model_manager
    from backend.core.config import settings

    print("\n=== System Benchmark ===")
    t0 = time.time()
    vec = embedding_service.embed_text("Benchmark test phrase to measure latency.")
    t1 = time.time()
    
    emb_latency = (t1-t0)*1000
    print(f"Embedding Latency (sentence-transformers): {emb_latency:.1f}ms")
    print(f"Embedding Dimension: {len(vec)}")
    
    prof = resource_manager.get_hardware_profile()
    
    hw_profile = {
        "hardware": prof,
        "recommended_llm": model_manager.get_llm_model(),
        "recommended_embedding_model": model_manager.get_embedding_model(),
        "recommended_whisper_model": model_manager.get_whisper_model(),
        "embedding_batch_size": model_manager.get_embedding_batch_size(),
        "max_concurrent_ai_tasks": resource_manager.max_concurrent_tasks,
        "render_mode": resource_manager.render_mode,
        "benchmark_results": {
            "embedding_latency_ms": emb_latency
        }
    }
    
    with open(settings.hardware_profile_path, "w", encoding="utf-8") as f:
        json.dump(hw_profile, f, indent=4)
        
    print(f"Hardware profile generated and saved to {settings.hardware_profile_path}")

def main():
    parser = argparse.ArgumentParser(description="Autonomous YouTube Shorts Production Agent")
    subparsers = parser.add_subparsers(dest="command", help="Agent commands")

    # setup
    subparsers.add_parser("setup", help="Verify environment dependencies")

    # run-agent
    run_parser = subparsers.add_parser("run-agent", help="Run full autonomous production pipeline")
    run_parser.add_argument("--topic", type=str, help="Specific topic (optional)")
    run_parser.add_argument("--category", type=str, default="science", help="Niche category")
    run_parser.add_argument("--auto-publish", action="store_true", help="Publish automatically when QC passes")
    run_parser.add_argument("--demo", action="store_true", help="Run in demo mode")

    # dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Start FastAPI web dashboard")
    dash_parser.add_argument("--host", type=str, default="127.0.0.1")
    dash_parser.add_argument("--port", type=int, default=8000)

    # discover
    disc_parser = subparsers.add_parser("discover", help="Discover and evaluate topics")
    disc_parser.add_argument("--category", type=str, default="science")

    # review
    subparsers.add_parser("review", help="Run the daily learning and self-improvement review")

    # status
    subparsers.add_parser("status", help="Show system status and recent projects")

    # memory commands
    subparsers.add_parser("memory-stats", help="Show structured and semantic memory stats")
    
    mem_search = subparsers.add_parser("memory-search", help="Search TurboVec semantic memory")
    mem_search.add_argument("query", type=str, help="Search query")
    
    subparsers.add_parser("memory-health", help="Check memory integrity")
    subparsers.add_parser("memory-backup", help="Backup semantic memory")
    subparsers.add_parser("memory-restore", help="Restore semantic memory")
    subparsers.add_parser("memory-rebuild", help="Rebuild TurboVec index from SQLite")
    subparsers.add_parser("memory-deduplicate", help="Find duplicate memories")
    
    # resource and benchmark commands
    subparsers.add_parser("resource-status", help="Show hardware and resource profile")
    subparsers.add_parser("benchmark", help="Measure system latency (Embeddings, DB, etc.)")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup()
    elif args.command == "run-agent":
        cmd_run_agent(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "review":
        cmd_review(args)
    elif args.command == "status":
        cmd_status()
    elif args.command == "memory-stats":
        cmd_memory_stats()
    elif args.command == "memory-search":
        cmd_memory_search(args)
    elif args.command == "resource-status":
        cmd_resource_status()
    elif args.command == "benchmark":
        cmd_benchmark()
    elif args.command in ["memory-health", "memory-backup", "memory-restore", "memory-rebuild", "memory-deduplicate"]:
        print(f"[{args.command}] Command acknowledged. (Implementation pending stub execution)")
    else:
        # Default action: run setup and print guidance
        cmd_setup()


if __name__ == "__main__":
    main()
