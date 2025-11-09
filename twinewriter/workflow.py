"""Workflow construction and run utilities for TwineWriter."""
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .models import AgentState
from .nodes import (
    input_node,
    content_generation_node,
    length_checker_node,
    thread_splitter_node,
    human_review_node,
    revision_node,
    finalizer_node,
)


def should_split_thread(state: AgentState) -> Literal["split_thread", "review"]:
    """Route to thread splitter if needed"""
    if state.get("error"):
        return "review"
    return "split_thread" if not state.get("tweets") else "review"


def should_revise(state: AgentState) -> str:
    """Route based on human decision"""
    if state.get("error"):
        return END
    if state.get("needs_revision"):
        return "revise"
    if state.get("approved"):
        return "finalize"
    return "review"  # Loop back for another review


def create_graph():
    """Build the LangGraph workflow"""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("input", input_node)
    workflow.add_node("generate", content_generation_node)
    workflow.add_node("check_length", length_checker_node)
    workflow.add_node("split_thread", thread_splitter_node)
    workflow.add_node("review", human_review_node)
    workflow.add_node("revise", revision_node)
    workflow.add_node("finalize", finalizer_node)

    # Define edges
    workflow.set_entry_point("input")
    workflow.add_edge("input", "generate")
    workflow.add_edge("generate", "check_length")
    workflow.add_conditional_edges("check_length", should_split_thread)
    workflow.add_edge("split_thread", "review")
    workflow.add_conditional_edges("review", should_revise)

    # After revision, re-check length and split if needed
    workflow.add_edge("revise", "check_length")
    workflow.add_edge("finalize", END)

    # Add memory for checkpointing
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)


def run_twinewriter(topic: str, tone: str = "professional", base_content: str = ""):
    """Run the TwineWriter agent and return final JSON if approved."""

    # Create initial state
    initial_state = {
        "topic": topic,
        "tone": tone,
        "base_content": base_content,
        "max_tweet_length": 280,
        "raw_content": "",
        "tweets": [],
        "human_feedback": "",
        "needs_revision": False,
        "approved": False,
        "final_json": {},
        "error": "",
    }

    # Create and run graph
    graph = create_graph()

    config = {"configurable": {"thread_id": "twinewriter-session"}}

    final_state = None
    for state in graph.stream(initial_state, config):
        final_state = state

    # Extract final state from the last node
    if final_state:
        last_node = list(final_state.keys())[-1]
        final_state = final_state[last_node]

    if final_state and final_state.get("approved") and not final_state.get("error"):
        return final_state["final_json"]
    else:
        return None
