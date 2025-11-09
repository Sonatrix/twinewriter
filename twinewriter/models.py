"""Data models for TwineWriter"""
from typing import TypedDict, List
from pydantic import BaseModel, Field


class TweetItem(BaseModel):
    """Single tweet in a thread"""
    index: int = Field(description="Position in thread (1-based)")
    content: str = Field(description="Tweet content")
    char_count: int = Field(description="Character count")

    def __str__(self):
        return f"[{self.index}] {self.content} ({self.char_count} chars)"


class AgentState(TypedDict):
    """State passed between nodes in the graph"""
    # Input
    topic: str
    tone: str  # professional, educational, witty, marketing, storytelling, casual
    base_content: str  # Optional pre-written content
    max_tweet_length: int  # Default 280

    # Generated content
    raw_content: str
    tweets: List[TweetItem]

    # Human review
    human_feedback: str
    needs_revision: bool
    approved: bool

    # Final output
    final_json: dict
    error: str
