# Terraform Policy (Terraform-specific)

Coding, security, and Terraform CI rules.
See also: `agents/agent-policy.md` (agent authority), `platform/platform-policy.md` (PR / detect-remediate pattern).

## Formatting
- Always run `terraform fmt` before merge.
- Use 2-space indentation.
- Keep resource blocks consistent; do not invent spacing inside identifiers.

## Security baseline (S3 example)
- Block public access by default.
- Enable encryption at rest (AES256 or KMS).
- Deny insecure transport (require HTTPS).
- Prefer versioning for critical buckets.

## Terraform CI & auto-heal
- CI must fail visibly when `terraform fmt -check` detects drift (detect job).
- Auto-heal is allowed for Terraform **formatting only** (indentation, whitespace).
- Auto-heal must not change resource logic, IAM, security rules, or topology.
- After a successful fmt re-check, the heal job may open a PR (merge follows platform policy).

## Apply restrictions
- CI workflows must never run `terraform apply` for this PoC / non-prod agent flow.
- Unsupervised agent apply is forbidden under `agents/agent-policy.md` production safety.
