"""
Run PlanAgent only — no architect / implementor / security.

Use this to learn how RAG feeds the plan:

  export PYTHONPATH=.
  python -m src.rag.ingest          # build knowledge index once
  python -m src.run_plan --prompt "Design a bank-safe Terraform fmt auto-heal CI"

Outputs:
  docs/generated/rag-context.md  — what RAG retrieved
  docs/generated/plan.md         — PlanAgent answer
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PlanAgent only (with visible RAG)")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Goal for the plan agent",
    )
    parser.add_argument(
        "--rag-only",
        action="store_true",
        help="Only show RAG retrieval — do not call Claude",
    )
    args = parser.parse_args()

    from src.agents.nodes import _save, plan_node
    from src.tools.repo_tools import search_knowledge

    print("=== 1) RAG retrieval ===")
    print(f"Query: {args.prompt}\n")
    rag = search_knowledge.invoke({"query": args.prompt})
    print(rag)
    print()
    _save("rag-context.md", rag)

    if args.rag_only:
        print("[info] --rag-only set; skipping Claude / PlanAgent.")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "Missing ANTHROPIC_API_KEY.\n"
            "Copy .env.example → .env, add your key, then re-run.\n"
            "Or try: python -m src.run_plan --rag-only --prompt \"...\""
        )

    print("=== 2) PlanAgent (Claude + RAG context) ===")
    result = plan_node(
        {
            "prompt": args.prompt,
            "retry_count": 0,
            "tool_logs": [],
        }
    )

    print("\n=== PLAN ===")
    print(result.get("plan", ""))
    print("\nTool logs:")
    for line in result.get("tool_logs") or []:
        print(f"  - {line}")
    print("\nArtifacts: docs/generated/rag-context.md and docs/generated/plan.md")


if __name__ == "__main__":
    main()
