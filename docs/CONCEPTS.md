# Concepts: LangChain PoC for beginners (Python OK)

This document explains **ideas first**, then points to files in this repo.

---

## 1. What is LangChain?

**LangChain is a Python library**, not a new language.

You still write Python. LangChain gives ready-made pieces for LLM apps:

| Piece | Plain English |
|-------|----------------|
| Chat model | Call Claude/OpenAI with messages |
| Prompt / SystemMessage | Instructions to the model |
| Tool | A Python function the model (or your code) can run |
| Retriever / Vector store | Search your docs (RAG) |
| Document loader / splitter | Load and chunk files |

**In this repo:** `langchain-anthropic`, `langchain-core`, `langchain-community`.

---

## 2. What is LangGraph?

**LangGraph** (also Python) controls **workflow**:

- Which step runs next
- Shared **state** (a dict that travels between steps)
- Loops (e.g. Security FAIL → Implementor again)

Think flowchart:

```text
plan → architect → implementor → security → (pass? end : retry)
```

**In this repo:** `src/graph/delivery_graph.py` + `src/graph/state.py`.

### LangChain vs LangGraph (remember this)

- **LangChain** = bricks (LLM, tools, RAG)
- **LangGraph** = the building plan (flow control)

---

## 3. What is an “agent” here?

In AutoGen you used `AssistantAgent(...)`.

Here, each agent is mostly a **Python function (node)** that:

1. Reads shared state  
2. Calls tools / RAG  
3. Calls Claude  
4. Writes markdown + returns state updates  

**In this repo:** `src/agents/nodes.py` (`plan_node`, `architect_node`, …).

---

## 4. What are tools?

A **tool** is a normal Python function wrapped so LangChain knows its name/description.

Example: `terraform_fmt_check` runs the real CLI and returns the output string.

**In this repo:** `src/tools/repo_tools.py` (`@tool` decorator).

Teaching pattern used in Implementor/Security:

> We call tools **in Python first**, then give results to Claude.  
> Later you can learn `bind_tools` so the *model* chooses which tool to call.

---

## 5. What is RAG?

**Retrieval-Augmented Generation**:

1. Put policy docs in `knowledge/`  
2. Split + embed + store in FAISS (`rag_index/`)  
3. At runtime, search similar chunks  
4. Put chunks into the prompt so Claude answers from **your docs**, not only memory  

**In this repo:**

- docs: `knowledge/*.md`  
- ingest: `python -m src.rag.ingest`  
- search: `search_knowledge` tool / `src/rag/retriever.py`

---

## 6. What is MCP?

**Model Context Protocol** = standard way for AI apps to use external **tool servers**.

Example: GitHub MCP server → create PR, list runs.

**In this PoC Phase 1:** `src/mcp/github_client.py` is an **educational stub** using GitHub REST API (same *role* as MCP tools). You can later swap in a real MCP client without changing the LangGraph design.

---

## 7. Terraform auto-heal pipeline

GitHub Actions:

1. **Detect job** runs `terraform fmt -check` — **fails red** if drift  
2. **Heal job** runs `scripts/claude_fmt_heal.py` (LangChain + Claude)  
3. Opens a PR with formatting fixes  

**Bank story:** detect fails for visibility; heal is formatting-only; humans review PR.

---

## 8. AutoGen vs this PoC (interview)

| Topic | Your AutoGen PoC | This LangChain PoC |
|-------|------------------|--------------------|
| Agent creation | `AssistantAgent` | Graph nodes + ChatAnthropic |
| Orchestration | Python awaits / RoundRobin | **LangGraph** edges |
| Debate chat | Strong (RoundRobin) | Not the focus (pipeline + retry) |
| Tools / RAG | Light / custom | **First-class** |
| CI heal | Claude scripts | Same idea, LangChain heal script |

---

## 9. Mental model diagram

```text
You (Python)
  └─ LangGraph app.invoke(state)
        ├─ plan_node      → uses RAG tool + Claude
        ├─ architect_node → Claude
        ├─ implementor    → tools + Claude
        └─ security       → RAG + tools + Claude → PASS/FAIL
              └─ if FAIL and retries < 2 → implementor again
```
