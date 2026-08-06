# Platform Policy (common — GitHub, CI, secrets)

Shared platform rules (GitHub, CI, secrets). Agent rules: `agents/agent-policy.md`.
Tech rules (e.g. Terraform): `tech/terraform-policy.md`.

## GitHub & change management
- All production-impacting changes must go through a Pull Request.
- Prefer propose-via-PR over direct writes to main.
- Protected branches require human review before merge.

## CI detect & remediate pattern
- CI should fail visibly when a required check detects policy drift (detect job).
- Automated remediation jobs may open a PR after a successful re-check.
- Humans review and merge remediation PRs; pipelines must not auto-merge them.

## Secrets
- Secrets stay in a vault or CI secret store.
- Never commit secrets; avoid printing secrets in CI logs.
