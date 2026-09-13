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

        question_triggers = [
            r"part\s*2",
            r"what\s+about\s+(.+)",
            r"can\s+you\s+do\s+(.+)",
            r"how\s+does\s+(.+)\s+work",
            r"why\s+does\s+(.+)",
            r"what\s+happens\s+if\s+(.+)",
            r"is\s+it\s+true\s+that\s+(.+)",
        ]

        for c in comments:
            text = c.get("text", "").strip()
            author = c.get("author", "Viewer")
            if not text or len(text) < 6:
                continue

            matched = False
            derived = ""
            category = "science"

            # Check regex patterns
            for pat in question_triggers:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    matched = True
                    groups = m.groups()
                    if groups and groups[0]:
                        subject = groups[0].strip("?!. ")
                        derived = f"The Truth About {subject.title()}"
                    else:
                        derived = f"Part 2: Deep Dive into {text[:30]}..."
                    break

            if not matched and "?" in text and len(text.split()) >= 4:
                matched = True
                derived = f"Answering Viewer Question: {text.strip('?!. ').title()}"

            if matched and derived:
                # Infer category
                cat_lower = derived.lower()
                if any(w in cat_lower for w in ["space", "planet", "moon", "star", "nasa"]):
                    category = "space"
                elif any(w in cat_lower for w in ["ai", "robot", "computer", "code", "tech"]):
                    category = "technology"
                elif any(w in cat_lower for w in ["animal", "dog", "cat", "creature"]):
                    category = "animals"
                elif any(w in cat_lower for w in ["game", "playstation", "xbox", "gta"]):
                    category = "gaming"
                elif any(w in cat_lower for w in ["funny", "joke", "laugh"]):
                    category = "humor"
                else:
                    category = "science"

                candidate = CommentTopicCandidate(
                    original_comment=text,
                    author=author,
                    derived_topic=derived,
                    category=category,
                    opportunity_score=86.5,
                )
                candidates.append(candidate)

                # Persist into database
                add_comment_idea(
                    comment_text=text,
                    author=author,
                    derived_topic=derived,
                )

        logger.info(f"Comment Engine derived {len(candidates)} new topic ideas from {len(comments)} comments.")
        return candidates

    def get_pending_topics(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns pending viewer-suggested topics from database."""
        return get_pending_comment_ideas(limit=limit)


comment_engine = CommentEngine()
