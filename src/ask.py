"""
General RAG Q&A — ask anything against the knowledge base.

Usage (from repo root):

  export PYTHONPATH=.
  python -m src.ask --prompt "What does our terraform policy say about apply?"
  python -m src.ask --rag-only --prompt "Summarize platform PR rules"

Unlike Plan/Architect/Implementor, this is a free-form question path:
  prompt → RAG (top-k) → (optional) Claude answer grounded in chunks
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
    parser = argparse.ArgumentParser(description="Ask the knowledge base (RAG ± Claude)")
    parser.add_argument("--prompt", required=True, help="Your question")
    parser.add_argument(
        "--rag-only",
        action="store_true",
        help="Only retrieve and save chunks — do not call Claude",
    )
    args = parser.parse_args()

    from src.agents.nodes import _invoke, _save
    from src.tools.repo_tools import search_knowledge

    print("=== RAG retrieval ===")
    print(f"Query: {args.prompt}\n")
    rag = search_knowledge.invoke({"query": args.prompt})
    print(rag)
    print()
    _save("rag-context.md", rag)

    if args.rag_only:
        print("[info] --rag-only set; skipping Claude.")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "Missing ANTHROPIC_API_KEY. Set it in .env, or use --rag-only."
        )

    print("=== Answer (Claude + RAG) ===")
    system = (
        "You answer using the retrieved knowledge when possible.\n"
        "Cite source file names from the chunks.\n"
        "If the knowledge base does not cover something, say "
        '"Not covered by knowledge base".\n'
        "Do not invent org policy."
    )
    user = (
        f"Question:\n{args.prompt}\n\n"
        f"Retrieved knowledge (RAG):\n{rag}\n"
    )
    answer = _invoke(system, user)
    _save("ask-answer.md", answer)
    print(answer)
    print("\nArtifacts: docs/generated/rag-context.md and docs/generated/ask-answer.md")


if __name__ == "__main__":
    main()
