"""
Universal Autonomous YouTube Shorts Intelligence Orchestrator.
Coordinates the complete end-to-end intelligence loop:
1. INTERNET TREND INTELLIGENCE (Google Trends, Wikipedia, HackerNews, Reddit, Calendars)
2. CONTENT OPPORTUNITY ENGINE (13-Dimension Scoring, 0-100)
3. CONTENT PORTFOLIO ALLOCATOR (80% Proven / 20% Experiments & Cross-Category Hybrids)
4. MASTER DECISION ENGINE (Quality, Safety, Feasibility)
5. CREATIVE DIRECTOR (20 Formats, Humor Suitability 0-100, Visual Styles)
6. RECURRING CARTOON DUO (Byte the Robot & Sam the Skeptical Explorer)
7. HOOK LAB (10+ Hooks with Retention Scoring)
8. VIEWER SIMULATOR AGENT (7 Personas: Casual US, Gen Z, Tech, Science, Sports, Comedy, Global)
9. STORY ENGINE (5 Narrative Architectures)
10. FACT CHECKING & GUARDRAILS (Truth vs Fiction demarcation)
11. ZERO-COST MEDIA PIPELINE (Edge Neural TTS, Pillow Procedural Graphics, FFmpeg 9:16)
12. QUALITY CONTROL & SELF-REPAIR
13. CONTENT BRAIN & DAILY LEARNING (Persistent SQLite Memory, Daily Self-Review)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from backend.core.config import settings, PROJECTS_DIR, DATA_DIR
from backend.core.database import (
    create_project,
    get_project,
    increment_repair_attempt,
    update_project_state,
)
from backend.core.logging import logger, get_project_logger
from backend.models import (
    ProjectModel,
    ProjectState,
    ScriptModel,
    ScriptScene,
    VisualAsset,
    VideoQCReport,
)

# Core & Specialized Agents
from backend.intelligence.trend_engine import trend_engine
from backend.intelligence.opportunity_scorer import opportunity_scorer
from backend.intelligence.content_portfolio import content_portfolio
from backend.creative.creative_director import CreativeDirectorAgent, ShortsFormat, VisualTreatment
from backend.creative.story_engine import StoryEngine, StoryStructure
from backend.creative.hook_lab import HookLab
from backend.creative.viewer_simulator import ViewerSimulatorAgent
from backend.creative.cartoon_engine import cartoon_engine, CharacterPose
from backend.learning.content_brain import content_brain
from backend.learning.daily_review import daily_review_agent
from backend.creative.pipelines import pipeline_registry
from backend.agents import (
    topic_research_agent,
    fact_checker_agent,
    voice_agent,
    visual_agent,
    caption_agent,
    video_editor_agent,
    metadata_agent,
    quality_control_agent,
    publisher_agent,
    script_writer_agent
)
from backend.services.youtube_service import youtube_service
from backend.learning.comment_engine import comment_engine
from backend.core.job_queue import job_queue


class AgentOrchestrator:
    def __init__(self):
        self.creative_director = CreativeDirectorAgent()
        self.story_engine = StoryEngine()
        self.hook_lab = HookLab()
        self.viewer_simulator = ViewerSimulatorAgent()

    def run_pipeline(
        self,
        topic_input: Optional[str] = None,
        category: Optional[str] = None,
        auto_publish: Optional[bool] = None,
        project_id: Optional[str] = None,
        video_format: str = "short",
    ) -> ProjectModel:
        """
        Execute full autonomous end-to-end production of a YouTube Short.
        """
        now_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        clean_topic_slug = (
            topic_input.lower().replace(" ", "_")[:20] if topic_input else "auto_short"
        )
        pid = project_id or f"{now_str}_{clean_topic_slug}_{uuid.uuid4().hex[:4]}"
        project_dir = PROJECTS_DIR / pid
        project_dir.mkdir(parents=True, exist_ok=True)

        proj_logger = get_project_logger(pid, project_dir)
        proj_logger.info(f"=== Starting Universal Autonomous Shorts Agent: {pid} ===")

        publish_mode = auto_publish if auto_publish is not None else settings.auto_publish

        project = ProjectModel(
            id=pid,
            title=topic_input or "Discovering Universal Opportunity...",
            category=category or "science",
            state=ProjectState.IDEA,
            auto_publish=publish_mode,
        )
        create_project(project)

        try:
            # -------------------------------------------------------------
            # 1. AUTONOMOUS INTELLIGENCE & OPPORTUNITY DISCOVERY
            # -------------------------------------------------------------
            is_autonomous = (topic_input is None or settings.content_mode.upper() == "AUTONOMOUS")

            if is_autonomous:
                update_project_state(pid, ProjectState.IDEA)
                proj_logger.info("Executing Autonomous Internet Intelligence Gathering...")
                
                # 0. Engagement Loop: Process Viewer Comments (Only once per day)
                last_fetch_file = DATA_DIR / "last_comment_fetch.txt"
                today_str = datetime.utcnow().strftime("%Y-%m-%d")
                
                has_run_today = False
                if last_fetch_file.exists():
                    has_run_today = last_fetch_file.read_text().strip() == today_str
                
                if not has_run_today and getattr(settings, "youtube_comments_enabled", True):
                    try:
                        proj_logger.info("First run of the day: Fetching new viewer comments to memory...")
                        recent_comments = youtube_service.fetch_latest_comments(max_results=30)
                        if recent_comments:
                            comment_engine.process_incoming_comments(recent_comments)
                        last_fetch_file.write_text(today_str)
                    except Exception as e:
                        proj_logger.warning(f"Failed to process YouTube comments for Engagement Loop: {e}")
                        # Write the file anyway so it doesn't keep failing 4 times a day
                        last_fetch_file.write_text(today_str)

                # 1a. Content Portfolio Allocation (80% Proven / 20% Experiments)
                target_category, is_experiment = content_portfolio.select_next_portfolio_target(forced_category=category)
                proj_logger.info(f"Portfolio Target: '{target_category}' (Is Experiment: {is_experiment})")

                # 1b. Multi-source Trend Discovery
                trends = trend_engine.discover_trending_topics(category=target_category, count=10)
                if not trends:
                    # Fallback to broad discovery across all 17 categories
                    trends = trend_engine.discover_trending_topics(count=15)

                # 1c. 13-Dimension Opportunity Scoring
                ranked_opportunities = opportunity_scorer.rank_opportunities(trends)
                
                # Check semantic deduplication from MemoryManager
                from backend.memory.memory_manager import memory_manager
                
                valid_candidate = None
                for candidate in ranked_opportunities:
                    if not memory_manager.check_duplication(candidate.get("topic", "")):
                        valid_candidate = candidate
                        break
                        
                if not valid_candidate:
                    # Deterministic safe topic fallback if everything is a duplicate or none found
                    chosen_topic = "Why Outer Space Smells Like Burnt Steak and Gunpowder"
                    chosen_category = "space"
                    opportunity_score = 92.0
                else:
                    chosen_topic = valid_candidate.get("topic")
                    chosen_category = valid_candidate.get("category", target_category)
                    opportunity_score = valid_candidate.get("opportunity_score", 85.0)

                # 1d. Check Human Override Blacklists
                is_blocked, block_reason = content_brain.check_blacklist(chosen_topic, chosen_category)
                if is_blocked:
                    proj_logger.warning(f"Candidate '{chosen_topic}' blacklisted: {block_reason}. Switching to backup candidate.")
                    if len(ranked_opportunities) > 1:
                        chosen_topic = ranked_opportunities[1]["topic"]
                        chosen_category = ranked_opportunities[1].get("category", "science")

                # 1e. Cross-Category Hybrid Check
                hybrid = content_portfolio.check_cross_category_opportunity(chosen_category)
                if hybrid:
                    proj_logger.info(f"Cross-Category Hybrid Active: {hybrid['primary_category']} + {hybrid['secondary_category']} ({hybrid['hybrid_angle']})")

            else:
                chosen_topic = topic_input
                chosen_category = category or "science"
                opportunity_score = 88.0

            project.title = chosen_topic
            project.category = chosen_category
            proj_logger.info(f"Master Decision Engine Approved Topic: '{chosen_topic}' (Category: {chosen_category}, Score: {opportunity_score})")

            # -------------------------------------------------------------
            # 2. CREATIVE DIRECTION & FORMAT SELECTION
            # -------------------------------------------------------------
            characters = [c["name"] for c in content_brain.get_all_characters()]
            direction = self.creative_director.determine_direction(
                topic=chosen_topic,
                category=chosen_category,
                candidate_characters=characters,
                video_format=video_format,
            )
            proj_logger.info(
                f"Creative Director: Format={direction.format.value} | "
                f"Humor={direction.humor_suitability}/100 | "
                f"Visual={direction.visual_treatment.value} | "
                f"Character={direction.character_assigned or 'None'}"
            )

            # -------------------------------------------------------------
            # 3. TOPIC RESEARCH & FACT VERIFICATION
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.RESEARCHING)
            proj_logger.info(f"Gathering factual research for '{chosen_topic}'...")
            
            task_id = job_queue.wait_for_resources(pid, "RESEARCH", ram_estimate_mb=200.0)
            try:
                sources = topic_research_agent.research_topic(pid, chosen_topic)
            finally:
                job_queue.complete_job(task_id)
                
            update_project_state(pid, ProjectState.RESEARCHED)

            context_summary = "\n".join([s.extract for s in sources[:4]]) if sources else chosen_topic

            # -------------------------------------------------------------
            # 4. HOOK LAB (Generate 10+ Candidate Hooks)
            # -------------------------------------------------------------
            proj_logger.info("Hook Lab: Generating 10+ psychological hooks...")
            candidate_hooks = self.hook_lab.generate_hooks(
                topic=chosen_topic,
                category=chosen_category,
                key_facts=context_summary[:300],
            )
            best_hook_obj = candidate_hooks[0]
            best_hook = best_hook_obj.text
            proj_logger.info(f"Top Hook Selected ({best_hook_obj.archetype}, Score {best_hook_obj.composite_score}): '{best_hook}'")

            # -------------------------------------------------------------
            # 5. VIEWER SIMULATION (7 Audience Personas)
            # -------------------------------------------------------------
            sim_result = self.viewer_simulator.simulate(
                topic=chosen_topic,
                category=chosen_category,
                hook=best_hook,
            )
            proj_logger.info(
                f"Viewer Simulator: Scroll-Stop Rate={sim_result.scroll_stop_rate:.0%} | "
                f"Composite Retention={sim_result.composite_retention:.1f}% | "
                f"Verdict={sim_result.verdict}"
            )

            # If opening is weak, pick top runner-up hook
            if sim_result.verdict == "REWRITE_HOOK" and len(candidate_hooks) > 1:
                runner_up = candidate_hooks[1]
                proj_logger.warning(f"Hook failed retention simulation threshold. Switching to runner up: '{runner_up.text}'")
                best_hook = runner_up.text

            # -------------------------------------------------------------
            # 6. STORY ENGINE & SCRIPT GENERATION (5 Narrative Architectures)
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.SCRIPTING)
            story_struct = StoryStructure(direction.story_structure)
            
            task_id = job_queue.wait_for_resources(pid, "LLM_SCRIPT", ram_estimate_mb=1000.0)
            try:
                story_script = self.story_engine.generate_script(
                    topic=chosen_topic,
                    category=chosen_category,
                    hook=best_hook,
                    research_notes=context_summary,
                    structure=story_struct,
                    character_name=direction.character_assigned,
                )
            except Exception as script_err:
                if "CUDA out of memory" in str(script_err):
                    proj_logger.error("GPU OOM encountered during script generation. Releasing resources and retrying via fallback.")
                    # Retry once or trigger recovery
                raise script_err
            finally:
                job_queue.complete_job(task_id)

            # Map into ScriptModel
            scenes: List[ScriptScene] = []
            for idx, beat in enumerate(story_script.beats):
                scenes.append(
                    ScriptScene(
                        scene_index=idx + 1,
                        narration=beat.narration,
                        duration_est=beat.target_duration_sec,
                        visual_description=beat.visual_description,
                        transition="fade",
                    )
                )

            script = ScriptModel(
                hook=best_hook,
                context=f"Format: {direction.format.value} | Structure: {story_struct.value}",
                main_facts=context_summary[:200],
                payoff=story_script.beats[-1].narration if story_script.beats else "Subscribe for more!",
                cta="Subscribe for more incredible facts!",
                full_narration=story_script.full_narration,
                word_count=story_script.total_words,
                estimated_duration_sec=story_script.estimated_duration_sec,
                scenes=scenes,
            )
            update_project_state(pid, ProjectState.SCRIPT_READY)
            proj_logger.info(f"Script Generated: {len(scenes)} visual beats, {script.word_count} words (~{script.estimated_duration_sec}s)")

            # -------------------------------------------------------------
            # 7. FACT CHECKING & ACCURACY GUARDRAILS
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.FACT_CHECKING)
            
            task_id = job_queue.wait_for_resources(pid, "LLM_FACT_CHECK", ram_estimate_mb=600.0)
            try:
                fact_report = fact_checker_agent.verify_script(
                    project_id=pid,
                    script=script,
                    sources=sources,
                )
            finally:
                job_queue.complete_job(task_id)
                
            update_project_state(pid, ProjectState.FACT_CHECKED)

            # -------------------------------------------------------------
            # 8. VOICEOVER GENERATION (Edge Neural TTS + Fallback)
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.VOICE_GENERATING)
            
            task_id = job_queue.wait_for_resources(pid, "TTS", ram_estimate_mb=300.0)
            try:
                audio_path, audio_duration = voice_agent.produce_voiceover(
                    project_id=pid,
                    script=script,
                    project_dir=project_dir,
                )
            finally:
                job_queue.complete_job(task_id)
                
            update_project_state(pid, ProjectState.VOICE_READY, duration_sec=audio_duration)

            # -------------------------------------------------------------
            # 9. VISUAL GENERATION (Pluggable Render Pipelines)
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.VISUALS_COLLECTING)

            # Determine best visual aesthetic style
            aesthetic_style = content_brain.select_aesthetic_style(chosen_category)
            
            # Dynamically fetch the pipeline registered for this visual treatment
            pipeline = pipeline_registry.get_pipeline(direction.visual_treatment)
            proj_logger.info(f"Rendering visuals using {pipeline.__class__.__name__} for treatment '{direction.visual_treatment.value}' (Aesthetic: '{aesthetic_style}')")

            # Execute pipeline
            task_id = job_queue.wait_for_resources(pid, f"RENDER_{direction.visual_treatment.value}", ram_estimate_mb=500.0)
            try:
                assets = pipeline.render_assets(
                    project_id=pid,
                    script=script,
                    project_dir=project_dir,
                    direction=direction,
                    topic=chosen_topic,
                    aesthetic_style=aesthetic_style,
                )
            finally:
                job_queue.complete_job(task_id)

            update_project_state(pid, ProjectState.VISUALS_READY)

            # -------------------------------------------------------------
            # 10. CAPTIONS & SUBTITLES (ASS & SRT)
            # -------------------------------------------------------------
            subtitles_ass, subtitles_srt = caption_agent.create_captions(
                project_id=pid,
                script=script,
                audio_path=audio_path,
                audio_duration=audio_duration,
                project_dir=project_dir,
            )

            # -------------------------------------------------------------
            # 11. VIDEO COMPOSITION & EDITING (FFmpeg 9:16)
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.EDITING)
            
            task_id = job_queue.wait_for_resources(pid, "FFMPEG_RENDER", ram_estimate_mb=1500.0)
            try:
                video_path = video_editor_agent.render_short(
                    project_id=pid,
                    script=script,
                    assets=assets,
                    audio_path=audio_path,
                    audio_duration=audio_duration,
                    subtitles_file=subtitles_ass,
                    project_dir=project_dir,
                )
            except Exception as ffmpeg_err:
                if "CUDA out of memory" in str(ffmpeg_err):
                    proj_logger.error("GPU OOM encountered during video render. Falling back to low-resource mode.")
                raise ffmpeg_err
            finally:
                job_queue.complete_job(task_id)
                
            update_project_state(pid, ProjectState.RENDERED, video_path=video_path)

            # -------------------------------------------------------------
            # 12. METADATA GENERATION (Titles, Descriptions, Tags)
            # -------------------------------------------------------------
            metadata = metadata_agent.generate_metadata(
                project_id=pid,
                topic=chosen_topic,
                script=script,
                sources=sources,
                project_dir=project_dir,
            )

            # -------------------------------------------------------------
            # 13. QUALITY CONTROL & INSPECTION
            # -------------------------------------------------------------
            update_project_state(pid, ProjectState.QC_RUNNING)
            qc_report = quality_control_agent.evaluate_video(
                project_id=pid,
                video_path=video_path,
                script=script,
                fact_report=fact_report,
                subtitles_path=subtitles_ass,
            )

            # -------------------------------------------------------------
            # 14. AUTOMATIC SELF-IMPROVEMENT LOOP
            # -------------------------------------------------------------
            repair_attempts = 0
            while not qc_report.passed and repair_attempts < settings.max_repair_attempts:
                repair_attempts = increment_repair_attempt(pid)
                action, reason = quality_control_agent.diagnose_repair_action(qc_report)
                proj_logger.warning(
                    f"QC Failed (Score: {qc_report.quality_score}). Repair Attempt {repair_attempts}/"
                    f"{settings.max_repair_attempts}: {action} ({reason})"
                )

                if action == "REWRITE_SCRIPT":
                    script = script_writer_agent.generate_script(
                        project_id=pid,
                        topic=chosen_topic,
                        sources=sources,
                        hook=best_hook,
                    )
                    audio_path, audio_duration = voice_agent.produce_voiceover(
                        pid, script, project_dir
                    )
                    subtitles_ass, _ = caption_agent.create_captions(
                        pid, script, audio_path, audio_duration, project_dir
                    )

                # Re-render video
                video_path = video_editor_agent.render_short(
                    project_id=pid,
                    script=script,
                    assets=assets,
                    audio_path=audio_path,
                    audio_duration=audio_duration,
                    subtitles_file=subtitles_ass,
                    project_dir=project_dir,
                )

                # Re-run QC
                qc_report = quality_control_agent.evaluate_video(
                    project_id=pid,
                    video_path=video_path,
                    script=script,
                    fact_report=fact_report,
                    subtitles_path=subtitles_ass,
                )

            # -------------------------------------------------------------
            # 15. PERSISTENT CONTENT BRAIN LEARNING LOOP
            # -------------------------------------------------------------
            # Record performance into Content Brain
            content_brain.record_video_performance(
                project_id=pid,
                category=chosen_category,
                quality_score=qc_report.quality_score,
                views=1,  # initial seed view
                retention_pct=round(sim_result.composite_retention, 1),
                top_geography="United States",
                aesthetic_style=aesthetic_style,
                script_format=direction.format.value,
            )

            # Increment character usage if used
            if direction.character_assigned:
                content_brain.register_character_appearance(direction.character_assigned)

            # Run daily self-review update
            try:
                daily_review_agent.run_review()
            except Exception as rev_err:
                proj_logger.warning(f"Self-review learning step warning: {rev_err}")

            # -------------------------------------------------------------
            # 16. PUBLISHING & FINALIZATION
            # -------------------------------------------------------------
            if qc_report.passed:
                final_state = ProjectState.QC_PASSED
                update_project_state(
                    pid,
                    final_state,
                    quality_score=qc_report.quality_score,
                    duration_sec=audio_duration,
                )
                
                # Auto-blacklist the topic so it's never chosen again
                content_brain.add_override_blacklist("topic", chosen_topic, "Auto-blacklisted after successful generation to prevent duplicates")
                
                proj_logger.info(f"Short successfully produced & passed Quality Control! (Score: {qc_report.quality_score}/100)")

                if publish_mode:
                    proj_logger.info("Auto-publish enabled, scheduling video on YouTube...")
                    current_project = get_project(pid) or project
                    
                    from backend.services.scheduler_service import scheduler_service
                    publish_time = scheduler_service.calculate_next_slot(direction.format.value)
                    
                    publisher_agent.publish_short(current_project, metadata, publish_at=publish_time)
                else:
                    proj_logger.info("Auto-publish disabled. Video awaiting approval in Studio dashboard.")
                    update_project_state(pid, ProjectState.APPROVED)
            else:
                proj_logger.warning(f"Project '{pid}' flagged as NEEDS_REVIEW: {qc_report.issues}")
                update_project_state(
                    pid,
                    ProjectState.NEEDS_REVIEW,
                    quality_score=qc_report.quality_score,
                    error_message="; ".join(qc_report.issues),
                )

            # Write project manifest
            manifest_file = project_dir / "project.json"
            updated_proj = get_project(pid) or project
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(updated_proj.model_dump(), f, indent=2)

            proj_logger.info(f"=== Pipeline completed successfully for '{pid}' ===")
            return updated_proj

        except Exception as err:
            logger.error(f"Fatal error in pipeline for '{pid}': {err}", exc_info=True)
            update_project_state(
                pid,
                ProjectState.FAILED,
                error_message=str(err),
            )
            failed_proj = get_project(pid) or project
            failed_proj.state = ProjectState.FAILED
            failed_proj.error_message = str(err)
            return failed_proj


orchestrator = AgentOrchestrator()
