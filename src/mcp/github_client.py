"""
MCP (Model Context Protocol) — educational stub for GitHub.

What MCP is:
  A standard way for an AI app to call tools hosted by an MCP *server*.
  Example: GitHub MCP server exposes "create_pull_request", "list_issues", etc.

What this file is:
  A *learning stub* that shows where MCP fits. It uses the GitHub REST API
  with a Personal Access Token (same outcome as many GitHub MCP tools).

Later you can replace these functions with a real MCP client session
connected to the official GitHub MCP server — the *agent graph* stays the same;
only the tool backend changes.

Setup:
  1) Create a classic PAT on github.com with repo scope
  2) Put GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO in .env
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN in .env to call GitHub APIs / MCP-equivalent tools.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "poc-agenticai-langchain",
    }


def _request(method: str, url: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} failed: {e.code} {detail}") from e


def list_open_pull_requests(owner: str | None = None, repo: str | None = None) -> str:
    """MCP-equivalent tool: list open PRs on your repo."""
    owner = owner or os.getenv("GITHUB_OWNER", "")
    repo = repo or os.getenv("GITHUB_REPO", "")
    if not owner or not repo:
        return "Set GITHUB_OWNER and GITHUB_REPO in .env"
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&per_page=10"
    prs = _request("GET", url)
    if not prs:
        return "No open pull requests."
    lines = [f"#{p['number']} {p['title']} — {p['html_url']}" for p in prs]
    return "\n".join(lines)


def create_pull_request(
    title: str,
    head: str,
    base: str,
    body: str,
    owner: str | None = None,
    repo: str | None = None,
) -> str:
    """MCP-equivalent tool: open a PR (used conceptually by heal pipeline)."""
    owner = owner or os.getenv("GITHUB_OWNER", "")
    repo = repo or os.getenv("GITHUB_REPO", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    pr = _request(
        "POST",
        url,
        {"title": title, "head": head, "base": base, "body": body},
    )
    return f"Created PR #{pr.get('number')}: {pr.get('html_url')}"


if __name__ == "__main__":
    # Quick manual test: python -m src.mcp.github_client
    from dotenv import load_dotenv
    from pathlib import Path

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    print(list_open_pull_requests())
