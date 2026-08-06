"""
Agent *roles* as LangGraph nodes.

Concept difference vs AutoGen:
  AutoGen: AssistantAgent objects that chat.
  Here: each "agent" is a Python function (node) that:
    - reads shared state
    - optionally calls tools / RAG
    - calls Claude via LangChain
    - writes results back into state

LangChain ChatAnthropic = wrapper around Anthropic Messages API.
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import DeliveryState
from src.tools.repo_tools import (
    list_tf_files,
    read_repo_file,
    search_knowledge,
    terraform_fmt_check,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "docs" / "generated"


def _llm() -> ChatAnthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        temperature=0.2,
        api_key=api_key,
    )


def _save(name: str, text: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"[artifact] wrote {path}")


def _invoke(system: str, user: str) -> str:
    llm = _llm()
    msg = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return str(msg.content)


def plan_node(state: DeliveryState) -> dict:
    """
    PlanAgent: create an actionable plan.
    Always loads shared agent-policy + plan-agent-policy, then RAG for platform/tech.
    """
    agent_policy = read_repo_file.invoke(
        {"relative_path": "knowledge/agents/agent-policy.md"}
    )
    plan_policy = read_repo_file.invoke(
        {"relative_path": "knowledge/agents/plan-agent-policy.md"}
    )
    rag = search_knowledge.invoke({"query": state["prompt"]})
    system = (
        "You are PlanAgent.\n"
        "Follow Shared Agent Policy and Plan Agent Policy in the user message exactly.\n"
        "Also respect platform/tech policies in Retrieved knowledge (RAG).\n"
        "Do not fall back to a different plan template than Plan Agent Policy defines."
    )
    user = (
        f"Shared Agent Policy:\n{agent_policy}\n\n"
        f"Plan Agent Policy:\n{plan_policy}\n\n"
        f"User goal:\n{state['prompt']}\n\n"
        f"Retrieved knowledge (RAG):\n{rag}\n"
    )
    plan = _invoke(system, user)
    _save("plan.md", plan)
    return {
        "plan": plan,
        "rag_context": rag,
        "tool_logs": [
            "read_repo_file knowledge/agents/agent-policy.md",
            "read_repo_file knowledge/agents/plan-agent-policy.md",
            f"search_knowledge for plan: {len(rag)} chars",
        ],
        "retry_count": state.get("retry_count", 0),
    }


def architect_node(state: DeliveryState) -> dict:
    """
    ArchitectAgent: design from the plan + Mermaid.
    Always loads shared agent-policy + architecture-agent-policy.
    """
    agent_policy = read_repo_file.invoke(
        {"relative_path": "knowledge/agents/agent-policy.md"}
    )
    arch_policy = read_repo_file.invoke(
        {"relative_path": "knowledge/agents/architecture-agent-policy.md"}
    )
    system = (
        "You are ArchitectAgent.\n"
        "Follow Shared Agent Policy and Architecture Agent Policy in the user message exactly.\n"
        "Design from the Plan and any RAG context provided.\n"
        "Do not fall back to a different architecture template than Architecture Agent Policy defines."
    )
    user = (
        f"Shared Agent Policy:\n{agent_policy}\n\n"
        f"Architecture Agent Policy:\n{arch_policy}\n\n"
        f"Plan:\n{state.get('plan', '')}\n\n"
        f"RAG context (from upstream):\n{state.get('rag_context', '')}\n"
    )
    architecture = _invoke(system, user)
    _save("architecture.md", architecture)
    return {
        "architecture": architecture,
        "tool_logs": [
            "read_repo_file knowledge/agents/agent-policy.md",
            "read_repo_file knowledge/agents/architecture-agent-policy.md",
        ],
    }


def implementor_node(state: DeliveryState) -> dict:
    """
    ImplementorAgent: proposes code changes.
    Always loads shared agent-policy + implementor-agent-policy.
    Uses tools deterministically first, then Claude.
    """
    agent_policy = read_repo_file.invoke(
        {"relative_path": "knowledge/agents/agent-policy.md"}
    )
    impl_policy = read_repo_file.invoke(
        {"relative_path": "knowledge/agents/implementor-agent-policy.md"}
    )
    tf_list = list_tf_files.invoke({})
    fmt = terraform_fmt_check.invoke({})
    sample = ""
    # Read first tf file if present
    first = tf_list.splitlines()[0] if tf_list and "No " not in tf_list else ""
    if first.endswith(".tf"):
        sample = read_repo_file.invoke({"relative_path": first})

    # Prefer reading existing workflow when architecture mentions CI heal
    workflow_sample = read_repo_file.invoke(
        {"relative_path": ".github/workflows/terraform-fmt-heal.yml"}
    )

    system = (
        "You are ImplementorAgent.\n"
        "Follow Shared Agent Policy and Implementor Agent Policy in the user message exactly.\n"
        "Propose concrete file updates from the Architecture and tool evidence.\n"
        "Do not fall back to a different proposal template than Implementor Agent Policy defines."
    )
    user = (
        f"Shared Agent Policy:\n{agent_policy}\n\n"
        f"Implementor Agent Policy:\n{impl_policy}\n\n"
        f"Architecture:\n{state.get('architecture', '')}\n\n"
        f"Plan (optional upstream):\n{state.get('plan', '')}\n\n"
        f"Tool list_tf_files:\n{tf_list}\n\n"
        f"Tool terraform_fmt_check:\n{fmt}\n\n"
        f"Sample Terraform file content:\n{sample[:4000]}\n\n"
        f"Existing workflow (.github/workflows/terraform-fmt-heal.yml):\n"
        f"{workflow_sample[:6000]}\n\n"
        f"Security feedback (if any):\n{state.get('security', '(none)')}\n"
    )
    implementation = _invoke(system, user)
    _save("implementation.md", implementation)
    return {
        "implementation": implementation,
        "tool_logs": [
            "read_repo_file knowledge/agents/agent-policy.md",
            "read_repo_file knowledge/agents/implementor-agent-policy.md",
            f"list_tf_files => {tf_list[:200]}",
            f"terraform_fmt_check => {fmt[:300]}",
        ],
    }


def security_node(state: DeliveryState) -> dict:
    """SecurityAgent: PASS/FAIL with RAG + tool evidence."""
    policy = search_knowledge.invoke(
        {"query": "change management auto-heal formatting pull request policy"}
    )
    fmt = terraform_fmt_check.invoke({})

    system = (
        "You are SecurityCheckAgent.\n"
        "Review the implementation against policy.\n"
        "End with exactly one line: SECURITY_PASS or SECURITY_FAIL.\n"
        "List findings and remediations briefly."
    )
    user = (
        f"Implementation:\n{state.get('implementation', '')}\n\n"
        f"Policy (RAG):\n{policy}\n\n"
        f"fmt tool:\n{fmt}\n"
    )
    security = _invoke(system, user)
    _save("security-report.md", security)
    # PoC rule: FAIL wins if mentioned; otherwise PASS if mentioned; else FAIL safe-default
    upper = security.upper()
    if "SECURITY_FAIL" in upper:
        passed = False
    elif "SECURITY_PASS" in upper:
        passed = True
    else:
        passed = False

    return {
        "security": security,
        "security_pass": passed,
        "tool_logs": [f"security fmt => {fmt[:200]}"],
    }


def bump_retry(state: DeliveryState) -> dict:
    """Called on FAIL path before looping back to implementor."""
    return {"retry_count": int(state.get("retry_count", 0)) + 1}
