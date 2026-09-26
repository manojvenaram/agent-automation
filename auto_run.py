import os
import random
import datetime
from backend.agents.orchestrator import run_workflow
from backend.core.database import list_projects, create_project
from backend.services.llm_service import llm_service
from backend.core.logging import logger

def get_past_topics():
    try:
        projects = list_projects(limit=100)
        return [p.title.lower() for p in projects if p.title]
    except Exception as e:
        logger.warning(f"Could not load past projects: {e}")
        return []

def generate_unique_topic():
    past_topics = get_past_topics()
    
    prompt = f"""
    You are a viral YouTube Shorts producer.
    I need a completely new, mind-blowing, and obscure educational topic for a "Did you know?" style video.
    
    STRICT RULE: The topic MUST NOT be similar to any of these previously covered topics:
    {', '.join(past_topics) if past_topics else 'None so far.'}
    
    It should be highly engaging (science, history, technology, or psychology).
    Return ONLY the topic title, nothing else. Maximum 6 words.
    Example: The immortal jellyfish that ages backwards
    """
    
    for attempt in range(3):
        logger.info(f"Generating unique topic (Attempt {attempt+1})...")
        topic = llm_service.generate_text(prompt).strip().replace('"', '')
        
        # Strict exact or substring match check
        topic_lower = topic.lower()
        is_similar = False
        for past in past_topics:
            if topic_lower in past or past in topic_lower:
                is_similar = True
                break
                
        if not is_similar:
            return topic
            
    # Fallback to something completely random with timestamp if LLM fails
    return f"Fascinating Science Fact {datetime.datetime.now().strftime('%H%M%S')}"

if __name__ == "__main__":
    logger.info("--- AUTONOMOUS VIDEO GENERATOR STARTED ---")
    
    # 1. Generate a strictly unique topic
    topic = generate_unique_topic()
    logger.info(f"Selected Unique Topic: {topic}")
    
    # 2. Record it in the database immediately so it's not reused
    try:
        create_project(title=topic, category="Auto-Generated")
    except Exception:
        pass
        
    # 3. Run the complete pipeline
    run_workflow(topic)
    
    logger.info("--- AUTONOMOUS VIDEO GENERATOR COMPLETED ---")
