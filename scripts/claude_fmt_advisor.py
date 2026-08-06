#!/usr/bin/env python3
"""
Claude fmt advisor — analyze terraform fmt -check failure output.

Used by the heal workflow: Claude explains drift; terraform fmt applies the fix.
Does not edit .tf files and never prints secret values.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


SYSTEM = """You are a Terraform formatting advisor for a CI auto-heal pipeline.

Rules:
- Only discuss terraform fmt / formatting (indentation, whitespace, alignment).
- Do not suggest resource logic, IAM, security, or topology changes.
- Do not invent files that are not mentioned in the drift output.
- Do not request or repeat any API keys or secrets.
- Be concise and useful for a human reviewing an auto-heal PR.
"""


def build_user_prompt(drift: str) -> str:
    return f"""terraform fmt -check reported formatting drift (or listed files).
Produce a short analysis for the auto-heal Pull Request body.

Include:
1. Summary of what failed (1-3 sentences)
2. Files / regions that look misformatted (from the log)
3. What the heal job will do (`terraform fmt` only)
4. What the reviewer should verify before merge

Drift / check output:
```
{drift[:12000]}
```
"""


def call_claude(drift: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    try:
        import anthropic
    except ImportError as exc:
        raise SystemExit(
            "anthropic package missing; pip install anthropic"
        ) from exc

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_user_prompt(drift)}],
    )
    parts = []
    for block in message.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    if not parts:
        raise SystemExit("Claude returned empty analysis")
    return "\n".join(parts).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude Terraform fmt advisor")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to terraform fmt -check / -diff output",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write Claude analysis markdown",
    )
    args = parser.parse_args()

    drift_path = Path(args.input)
    if not drift_path.is_file():
        raise SystemExit(f"Input not found: {drift_path}")

    drift = drift_path.read_text(encoding="utf-8", errors="replace").strip()
    if not drift:
        drift = "(No fmt output captured; heal will still run terraform fmt.)"

    analysis = call_claude(drift)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(analysis, encoding="utf-8")
    # Safe summary only — never echo API material.
    print(f"Wrote Claude analysis to {out} ({len(analysis)} chars)")


if __name__ == "__main__":
    main()
    sys.exit(0)
