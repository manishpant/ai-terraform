"""
Shared graph STATE.

In LangGraph, every node reads/writes a shared dictionary-like state.
Think of it as a clipboard that travels through Plan → Architect → ...

Why TypedDict?
- Documents what keys exist (like a light type hint for interviews).
- Helps you explain "shared state" clearly vs AutoGen message-passing.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


def merge_lists(left: list[Any] | None, right: list[Any] | None) -> list[Any]:
    """Reducer: when two nodes append logs, merge instead of overwrite."""
    return (left or []) + (right or [])


class DeliveryState(TypedDict, total=False):
    """
    Shared state for the delivery graph.

    total=False means keys are optional at start; nodes fill them in.
    """

    # User's original ask
    prompt: str

    # Artifacts produced by each agent (markdown strings)
    plan: str
    architecture: str
    implementation: str
    security: str
    security_pass: bool

    # RAG snippets retrieved for grounding
    rag_context: str

    # Audit trail of tool / MCP calls (bank interview talking point)
    tool_logs: Annotated[list[str], merge_lists]

    # How many times we looped after Security FAIL
    retry_count: int

    # Optional chat-style messages if you extend the graph later
    messages: Annotated[list, add_messages]
