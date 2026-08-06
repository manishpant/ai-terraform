"""
LangChain TOOLS — actions the LLM can request.

Concept:
  LLM does not magically run terraform. You define Python functions,
  wrap them as tools, and bind them to an agent/model.
  The model returns a "tool call"; LangChain executes your function;
  the result goes back to the model.

This is the same *idea* as AutoGen tools or MCP tools — different wiring.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from langchain_core.tools import tool

# Repo root = three levels up from this file: src/tools -> src -> repo
REPO_ROOT = Path(__file__).resolve().parents[2]
TERRAFORM_DIR = REPO_ROOT / "terraform"
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"


def _safe_path(relative: str) -> Path:
    """
    Guardrail: only allow reading under the repo (no ../../../etc/passwd).
    Banks care about this — allowlist paths.
    """
    candidate = (REPO_ROOT / relative).resolve()
    if not str(candidate).startswith(str(REPO_ROOT.resolve())):
        raise ValueError(f"Path escapes repo: {relative}")
    return candidate


@tool
def list_tf_files() -> str:
    """List Terraform .tf files under terraform/ for the implementor/security agents."""
    if not TERRAFORM_DIR.exists():
        return "No terraform/ directory found."
    files = sorted(TERRAFORM_DIR.rglob("*.tf"))
    if not files:
        return "No .tf files found."
    return "\n".join(str(p.relative_to(REPO_ROOT)) for p in files)


@tool
def read_repo_file(relative_path: str) -> str:
    """
    Read a text file from this repository by relative path.
    Example: terraform/main.tf or knowledge/tech/terraform-policy.md
    """
    path = _safe_path(relative_path)
    if not path.exists():
        return f"File not found: {relative_path}"
    if path.stat().st_size > 200_000:
        return f"File too large to read in PoC: {relative_path}"
    return path.read_text(encoding="utf-8")


@tool
def terraform_fmt_check() -> str:
    """
    Run `terraform fmt -check -recursive` on terraform/.
    Returns exit code meaning:
      0 = already formatted
      non-zero (often 3) = files need formatting
    """
    if not TERRAFORM_DIR.exists():
        return "terraform/ missing — cannot run fmt."
    try:
        result = subprocess.run(
            ["terraform", "fmt", "-check", "-recursive", str(TERRAFORM_DIR)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
    except FileNotFoundError:
        return (
            "terraform CLI not installed on this machine. "
            "Install Terraform to use this tool locally; CI runners have it."
        )
    out = (result.stdout or "") + (result.stderr or "")
    return (
        f"exit_code={result.returncode}\n"
        f"output:\n{out.strip() or '(empty — exit 0 usually means clean)'}"
    )


@tool
def search_knowledge(query: str) -> str:
    """
    RAG tool: search local knowledge base for policies / Terraform standards.
    Uses simple keyword fallback if the vector index is not built yet.
    Prefer running: python -m src.rag.ingest   then search uses FAISS.
    """
    # Lazy import so `list_tf_files` still works if RAG deps missing briefly
    try:
        from src.rag.retriever import retrieve
        return retrieve(query, k=5)
    except Exception as exc:  # noqa: BLE001 — educational PoC: show errors to agent
        # Fallback: dumb keyword scan so demos still work before ingest
        chunks: list[str] = []
        if KNOWLEDGE_DIR.exists():
            q = query.lower()
            for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                if any(tok in text.lower() for tok in q.split() if len(tok) > 3):
                    chunks.append(f"### Source: {path.name}\n{text[:1200]}")
        if chunks:
            return "\n\n".join(chunks[:4])
        return f"RAG unavailable ({exc}). Put markdown files in knowledge/ and run ingest."


# Export list for binding to agents
ALL_TOOLS = [list_tf_files, read_repo_file, terraform_fmt_check, search_knowledge]
