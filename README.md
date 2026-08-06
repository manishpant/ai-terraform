# ai-terraform

Sibling PoC focused on **LangChain + LangGraph** for bank-safe Terraform formatting auto-heal CI (Claude as advisor + PR gate).

Repo: [manishpant/ai-terraform](https://github.com/manishpant/ai-terraform)

---

## What this PoC covers

| Topic | Status |
|-------|--------|
| Agents | Plan / Architect / Implementor / Security nodes |
| Orchestration | LangGraph with Security → retry loop |
| Tools | list/read tf, `terraform fmt -check`, RAG search |
| RAG | `knowledge/` → FAISS via `src.rag.ingest` |
| MCP (GitHub) | Educational stub (`src/mcp/github_client.py`) |
| Terraform auto-heal + Claude | Detect + heal GHA workflows + `scripts/claude_fmt_advisor.py` |

Read **[docs/CONCEPTS.md](docs/CONCEPTS.md)** first if you are new to LangChain.

---

## Prerequisites

- Python 3.11+
- Anthropic API key
- Optional: Terraform CLI (for local fmt tool)
- Optional: GitHub PAT (for MCP-style GitHub calls)

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env → set ANTHROPIC_API_KEY
export PYTHONPATH=.
python -m src.rag.ingest
```

---

## Run the agent graph

```bash
export PYTHONPATH=.
python -m src.app --prompt "Design a bank-safe Terraform fmt auto-heal CI using Claude and PRs"
```

---

## Terraform CI auto-heal (test)

1. Add secret `ANTHROPIC_API_KEY` in GitHub Actions secrets.
2. Ensure Actions can create PRs (Settings → Actions → General → Workflow permissions).
3. Push misformatted `terraform/*.tf` (already in this repo for the first test).
4. Watch: **detect** fails → **heal** (Claude analysis + `terraform fmt`) → PR opens.

Workflows:

- `.github/workflows/terraform-detect.yml`
- `.github/workflows/terraform-heal.yml`

See also [PIPELINE.md](PIPELINE.md).
