# Agent Policy (agent-specific)

Rules for AI agents (LangGraph / LangChain nodes, heal scripts that call models).
Platform GitHub/CI process: `platform/platform-policy.md`. Tech rules (e.g. Terraform): `tech/`.

## Authority
- Agents may *propose* plans, designs, code, and remediations.
- Humans *approve* merges via Pull Request review.
- Agents must not auto-merge to protected branches.

## Secrets & outputs
- Agents must not store or print secrets in prompts, tool results, or artifacts.
- Prefer referencing secret *names* (e.g. env var keys), never values.

## Tools & audit
- Agent tool calls and MCP-style actions should be logged (e.g. tool_logs).
- Agents should prefer read-only / check tools over mutating production systems.

## Production safety
- No unsupervised production apply or deploy from an agent.
- Destructive or production-impacting actions require a human-approved PR path.
