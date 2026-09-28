"""
Comment-to-Content Engine for YouTube Shorts Intelligence.
Transforms viewer comments, questions, and feedback loops into high-opportunity Short topics:
VIDEO -> COMMENTS -> VIEWER QUESTIONS -> NEW TOPICS -> NEXT GENERATION OF CONTENT

Recognizes questions, requests for sequels ("Part 2?"), counter-arguments, and deep-dive inquiries.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re
from backend.core.database import add_comment_idea, get_pending_comment_ideas
from backend.core.logging import logger
from backend.services.llm_service import LLMService


@dataclass
class CommentTopicCandidate:
    original_comment: str
    author: str
    derived_topic: str
    category: str
    opportunity_score: float
    status: str = "PENDING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_comment": self.original_comment,
            "author": self.author,
            "derived_topic": self.derived_topic,
            "category": self.category,
            "opportunity_score": round(self.opportunity_score, 1),
            "status": self.status,
        }


class CommentEngine:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.ollama = llm_service or LLMService()

    def process_incoming_comments(self, comments: List[Dict[str, str]]) -> List[CommentTopicCandidate]:
        """
        Parses list of comments [{'text': '...', 'author': '...'}] into new topic candidates.
        """
        candidates: List[CommentTopicCandidate] = []

        for c in comments:
            text = c.get("text", "").strip()
            author = c.get("author", "Viewer")
            if not text or len(text) < 6:
                continue

            prompt = (
                f"Analyze this YouTube comment: '{text}'\n"
                f"Is the viewer asking a question, requesting a sequel, or making a counter-argument that would make a good standalone YouTube Short video?\n"
                f"If yes, return a JSON object with 'is_idea': true, 'derived_topic': '<compelling title>', 'category': '<science|space|technology|gaming|humor|mystery>', and 'opportunity_score': <1-100 float> based on potential virality.\n"
                f"If no, return {{\"is_idea\": false}}.\n"
                f"Respond ONLY with valid JSON."
            )
            
            try:
                import json
                response = self.ollama.generate(prompt, json_mode=True)
                data = json.loads(response)
                
                # Autonomously reply to the viewer!
                comment_id = c.get("id")
                if comment_id:
                    reply_prompt = (
                        f"You are the creator of an AI-generated YouTube Shorts channel.\n"
                        f"A viewer named {author} just commented: '{text}'\n"
                        f"Write a witty, extremely brief (1-2 sentences), and highly engaging reply to them. Be somewhat mysterious but very polite. Don't use emojis."
                    )
                    try:
                        reply_text = self.ollama.generate(reply_prompt).strip()
                        if reply_text and len(reply_text) > 5:
                            from backend.services.youtube_service import youtube_service
                            youtube_service.reply_to_comment(comment_id, reply_text)
                    except Exception as e:
                        logger.error(f"Failed to generate/post reply: {e}")

                if data.get("is_idea") and data.get("derived_topic"):
                    candidate = CommentTopicCandidate(
                        original_comment=text,
                        author=author,
                        derived_topic=data["derived_topic"],
                        category=data.get("category", "science").lower(),
                        opportunity_score=float(data.get("opportunity_score", 80.0)),
                    )
                    candidates.append(candidate)

                    # Persist into database
                    add_comment_idea(
                        comment_text=text,
                        author=author,
                        derived_topic=data["derived_topic"],
                    )
            except Exception as e:
                logger.error(f"Failed to process comment with LLM: {e}")

        logger.info(f"Comment Engine derived {len(candidates)} new topic ideas from {len(comments)} unreplied comments.")
        return candidates

    def get_pending_topics(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns pending viewer-suggested topics from database."""
        return get_pending_comment_ideas(limit=limit)


comment_engine = CommentEngine()
