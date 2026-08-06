# poc-agenticai-langchain

Sibling PoC to `cursor-agents-poc`, focused on **LangChain + LangGraph**.

**Location:** `/Users/pratima/manish/poc-agenticai-langchain`  
(parallel to `/Users/pratima/manish/cursor-agents-poc`)

---

## What this PoC covers

| Topic | Status in this starter |
|-------|-------------------------|
| Agents | Plan / Architect / Implementor / Security nodes |
| Orchestration | LangGraph with Security → retry loop |
| Tools | list/read tf, `terraform fmt -check`, RAG search |
| RAG | `knowledge/` → FAISS via `src.rag.ingest` |
| MCP (GitHub) | Educational stub (`src/mcp/github_client.py`) ready for your account |
| Terraform auto-heal + Claude | GHA 2-job workflow + `scripts/claude_fmt_heal.py` |

Read **[docs/CONCEPTS.md](docs/CONCEPTS.md)** first if you are new to LangChain.

---

## Prerequisites

- Python 3.11+
- Anthropic API key
- Optional: Terraform CLI (for local fmt tool)
- Optional: GitHub PAT (for MCP-style GitHub calls)
- Optional: `gh` CLI (for Actions PR step)

---

## Setup (step by step)

```bash
cd /Users/pratima/manish/poc-agenticai-langchain

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# edit .env → set ANTHROPIC_API_KEY
```

Build the RAG index (downloads a small local embedding model first time):

```bash
export PYTHONPATH=.
python -m src.rag.ingest
```

---

## Run the agent graph

```bash
export PYTHONPATH=.
python -m src.app --prompt "Design a bank-safe Terraform fmt auto-heal CI using Claude and PRs"
```

Outputs appear in `docs/generated/`:

- `plan.md`
- `architecture.md`
- `implementation.md`
- `security-report.md`
- `run-summary.json`

---

## Test GitHub helper (MCP-equivalent)

```bash
# .env must have GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
python -m src.mcp.github_client
```

---

## Terraform CI auto-heal

1. Push this repo to **your** GitHub account.  
2. Add secret `ANTHROPIC_API_KEY`.  
3. Repo Settings → Actions → allow Actions to create PRs.  
4. Break formatting in `terraform/main.tf` (bad indentation) and push.  
5. Watch: **detect** fails → **heal** runs Claude → PR opens.

Workflow file: `.github/workflows/terraform-fmt-heal.yml`

---

## Learning path

1. Read `docs/CONCEPTS.md`  
2. Open `src/tools/repo_tools.py` — simplest “tool” idea  
3. Open `src/graph/state.py` + `delivery_graph.py` — orchestration  
4. Open `src/agents/nodes.py` — agents as functions  
5. Run ingest + `src.app`  
6. Read `scripts/claude_fmt_heal.py` + the workflow YAML  
7. Extend MCP stub or plug real GitHub MCP later  

---

## Interview one-liner

> I built a LangChain/LangGraph PoC where agents share state in a graph, use tools and RAG for evidence, call GitHub through an MCP-style boundary, and a Claude-powered GitHub Actions pipeline auto-heals Terraform formatting behind a failing detect job and a PR gate.
