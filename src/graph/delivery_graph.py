"""
LangGraph ORCHESTRATION — the workflow controller.

Visual flow:

  START → plan → architect → implementor → security
                                   ↑            │
                                   └── bump_retry ←─┘  (if FAIL and retries < 2)
                                                  │
                                                 END (if PASS or retries exhausted)

Compare to AutoGen:
  AutoGen RoundRobin = agents chat in turns.
  LangGraph = you draw edges and conditions yourself (audit-friendly for banks).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agents.nodes import (
    architect_node,
    bump_retry,
    implementor_node,
    plan_node,
    security_node,
)
from src.graph.state import DeliveryState


def _route_after_security(state: DeliveryState) -> str:
    """Conditional edge function: return the *name* of the next node."""
    if state.get("security_pass"):
        return "end"
    if int(state.get("retry_count", 0)) >= 2:
        return "end"  # stop looping — leave FAIL for humans
    return "retry"


def build_delivery_graph():
    graph = StateGraph(DeliveryState)

    # Register nodes (each is a Python function)
    graph.add_node("plan", plan_node)
    graph.add_node("architect", architect_node)
    graph.add_node("implementor", implementor_node)
    graph.add_node("security", security_node)
    graph.add_node("bump_retry", bump_retry)

    # Linear happy path
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "architect")
    graph.add_edge("architect", "implementor")
    graph.add_edge("implementor", "security")

    # Branch after security
    graph.add_conditional_edges(
        "security",
        _route_after_security,
        {
            "end": END,
            "retry": "bump_retry",
        },
    )
    graph.add_edge("bump_retry", "implementor")

    # compile() turns the definition into a runnable app
    return graph.compile()
