"""
CLI entrypoint for the PoC.

Usage (from repo root, with venv activated):

  export PYTHONPATH=.
  python -m src.app --prompt "Plan a safe Terraform fmt auto-heal CI for a bank PoC"

Concepts used:
  - dotenv loads ANTHROPIC_API_KEY
  - LangGraph compiled app.invoke(state) runs the workflow
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Ensure repo root imports work when run as module
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LangGraph delivery agents PoC")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Goal for Plan → Architect → Implementor → Security",
    )
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("Missing ANTHROPIC_API_KEY. Copy .env.example to .env first.")

    from src.graph.delivery_graph import build_delivery_graph

    app = build_delivery_graph()
    print("[info] Starting LangGraph delivery flow...")
    final_state = app.invoke(
        {
            "prompt": args.prompt,
            "retry_count": 0,
            "tool_logs": [],
        }
    )

    print("\n=== FLOW COMPLETE ===")
    print(f"security_pass={final_state.get('security_pass')}")
    print(f"retry_count={final_state.get('retry_count')}")
    print("Artifacts under docs/generated/")
    print("Tool logs:")
    for line in final_state.get("tool_logs") or []:
        print(f"  - {line}")

    summary_path = REPO_ROOT / "docs" / "generated" / "run-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "security_pass": final_state.get("security_pass"),
                "retry_count": final_state.get("retry_count"),
                "tool_logs": final_state.get("tool_logs"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[artifact] {summary_path}")


if __name__ == "__main__":
    main()
