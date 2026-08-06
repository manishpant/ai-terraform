# Terraform Formatting Auto-Heal CI Pipeline

## Overview

This document describes the Terraform formatting auto-heal CI pipeline for this repository. The pipeline detects formatting drift with `terraform fmt -check`, automatically heals formatting-only issues, opens a Pull Request for human review, and enforces branch protection to prevent auto-merge and unsupervised `terraform apply`.

**Key principle:** Detect → Heal → PR → Human Approval → Merge. No agent auto-merge. No `terraform apply` at any stage.

---

## Workflow Triggers

### Detect Job (`.github/workflows/terraform-detect.yml`)

**Triggers:**
- Push to **any** branch (if `.tf` files changed)
- Pull request targeting any branch (if `.tf` files changed)

**What it does:**
1. Checks out code.
2. Installs Terraform (latest stable).
3. Runs `terraform fmt -check -recursive` to detect formatting drift.
4. **Passes** (green checkmark) if all files are properly formatted.
5. **Fails** (red X) if formatting drift is detected.

**Output:**
- Logs show `terraform fmt -check` output (no secrets).
- Visible in GitHub Actions UI under the "Checks" tab on the PR or commit.

---

### Heal Job (`.github/workflows/terraform-heal.yml`)

**Triggers:**
- Detect job fails on **any** branch (auto-heal source branches are skipped to avoid loops).

**What it does:**
1. Checks out code at the commit that triggered detect.
2. Installs Terraform (latest stable).
3. Captures `terraform fmt -check -diff` output.
4. Calls **Claude as AI advisor** (`scripts/claude_fmt_advisor.py` + `ANTHROPIC_API_KEY`) to write a short analysis for the PR body.
5. Runs `terraform fmt -recursive` to reformat all `.tf` files (actual fix — not free-form Claude edits).
6. Re-checks formatting, then opens a PR via `peter-evans/create-pull-request` with:
   - Commit message: `"chore: terraform fmt"`
   - PR title: `"Auto-heal: Terraform formatting"`
   - PR body: Claude analysis + human review steps.
   - Branch: `terraform-fmt-auto-heal` (temporary; deleted after merge/close).

**Output:**
- PR is created and visible in the "Pull Requests" tab.
- PR cannot be auto-merged (branch protection enforces human review).
- Logs show `terraform fmt` / advisor status (API key is never printed).

---

## Branch Protection Rule

**Target:** `main` branch

**Rules:**
- Require ≥1 pull request review before merge.
- Dismiss stale PR approvals when new commits are pushed.
- Require status checks to pass:
  - `detect` (Terraform Detect Formatting Drift job)
- Prevent force pushes and deletions.
- **Auto-merge disabled** (no auto-merge option available).

**Effect:**
- All changes (including auto-heal PRs) require human review and approval.
- Detect job must pass before merge is allowed.
- No direct commits to `main` without PR.

---

## Control Flow

```
1. Developer pushes code to any branch (or opens PR)
   ↓
2. Detect job runs: terraform fmt -check
   ├─ If no drift → Detect passes (green ✓)
   │  └─ Pipeline idle; no further action.
   │
   └─ If drift detected → Detect fails (red ✗)
      ↓
3. Heal job triggers (on detect failure for that branch)
   ├─ Captures fmt -check/-diff output
   ├─ Claude advisor writes analysis for the PR body
   ├─ Runs terraform fmt to reformat files
   ├─ Commits changes: "chore: terraform fmt"
   └─ Opens PR into the failed branch: "Auto-heal: Terraform formatting"
      ↓
4. Human reviews PR in GitHub UI
   ├─ Verifies only formatting changed (no logic/IAM/security changes)
   ├─ Approves PR (≥1 review required when branch protection applies)
   └─ Manually merges via GitHub UI (no auto-merge)
      ↓
5. After merge, the target branch is updated with formatted code
   ↓
6. Detect job runs again on that branch
   └─ Detect passes (green ✓); pipeline idle.
```

---

## Troubleshooting

### Detect Job Failed: "terraform fmt -check" Detected Drift

**Symptom:** Detect job shows red X; logs show formatting differences.

**Cause:** Terraform files have formatting drift (indentation, whitespace, etc.).

**Resolution:**
1. Wait for heal job to trigger (usually within 1–2 minutes).
2. Review the auto-heal PR when it appears.
3. Verify that only formatting changed (no resource logic or security changes).
4. Approve and merge the PR via GitHub UI.
5. Detect job will re-run on the updated branch and pass.

**Manual fix (alternative):**
1. Check out the branch locally.
2. Run `terraform fmt -recursive` to reformat files.
3. Commit and push changes.
4. Detect job will re-run and pass.

---

### Heal Job Did Not Open a PR

**Symptom:** Detect job failed, but no PR was created.

**Cause:** Heal job may have failed silently, or branch protection may have blocked PR creation.

**Resolution:**
1. Check GitHub Actions logs for the heal job:
   - Go to Actions → Terraform Auto-Heal Formatting → Latest run.
   - Look for error messages in the "Create Pull Request" step.
2. If logs show permission errors, verify that the Actions runner has `pull-requests: write` permission.
3. If logs show no errors, check the "Pull Requests" tab to see if PR was created with a different name.
4. If PR was not created, manually run the heal job:
   - Go to Actions → Terraform Auto-Heal Formatting → Run workflow.
   - Select `main` branch and click "Run workflow".

---

### Detect Job Passes, But I Know Formatting Is Wrong

**Symptom:** Detect job shows green ✓, but files appear misformatted.

**Cause:** Terraform version mismatch, or `terraform fmt` has different defaults.

**Resolution:**
1. Run `terraform fmt -check -recursive` locally to verify formatting.
2. If local check fails, run `terraform fmt -recursive` to reformat.
3. Commit and push changes; detect job will fail and trigger heal.
4. Review and merge the auto-heal PR.

---

### PR Cannot Be Merged: "Checks Failed"

**Symptom:** PR shows "Checks failed" and merge button is disabled.

**Cause:** Detect job is failing on the PR branch (formatting drift detected).

**Resolution:**
1. The heal job will open a separate PR to fix formatting on the failed branch.
2. Merge the heal PR first.
3. Then rebase or update your PR/branch to include the formatted code.
4. Detect job will re-run and pass.

---

## Secret Management

### ANTHROPIC_API_KEY

**Storage:** GitHub Actions secret (Settings → Secrets and variables → Actions).

**Usage:** Required by the heal job for Claude advisor analysis (`${{ secrets.ANTHROPIC_API_KEY }}`).  
If the secret is missing, heal still runs `terraform fmt` and opens a PR with a short fallback note.

**Security:**
- Secret value is never printed in logs (GitHub Actions masks secrets automatically).
- Secret is only available to workflows in this repository.
- Secret is not included in PR descriptions or commit messages.

**Rotation:** If the secret needs to be rotated, update it in GitHub Settings; no workflow changes required.

---

## Manual Workflow Runs

### Run Detect Job Manually

1. Go to GitHub → Actions → Terraform Detect Formatting Drift.
2. Click "Run workflow" (top right).
3. Select branch (default: `main`).
4. Click "Run workflow".
5. Monitor the job in the Actions UI.

### Run Heal Job Manually

1. Go to GitHub → Actions → Terraform Auto-Heal Formatting.
2. Click "Run workflow" (top right).
3. Select branch (default: `main`).
4. Click "Run workflow".
5. Monitor the job; PR will be created if formatting changes are detected.

---

## Constraints & Guarantees

### What the Pipeline Does
- ✅ Detects formatting drift with `terraform fmt -check`.
- ✅ Asks Claude for a formatting-focused analysis of the failure (advisor).
- ✅ Automatically reformats files with `terraform fmt`.
- ✅ Opens a PR for human review (analysis in the PR body).
- ✅ Enforces branch protection (≥1 review, no auto-merge).
- ✅ Logs all actions for audit.

### What the Pipeline Does NOT Do
- ❌ Never runs `terraform apply` (no infrastructure changes).
- ❌ Never runs `terraform plan` (no plan output).
- ❌ Never runs `terraform validate` (no validation).
- ❌ Never auto-merges PRs (human approval is required).
- ❌ Never exposes secrets in logs or PR descriptions.
- ❌ Never makes direct commits to `main` (all changes via PR).

---

## FAQ

**Q: Can I disable the auto-heal pipeline?**
A: Yes. Disable the heal workflow in GitHub Actions settings, or delete `.github/workflows/terraform-heal.yml`. The detect job will still run and fail on formatting drift; you can fix formatting manually.

**Q: What if I want to use a different Terraform version?**
A: Edit both workflow files and change `terraform_version: latest` to a specific version (e.g., `terraform_version: 1.6.0`).

**Q: Can the heal PR be auto-merged?**
A: No. Branch protection enforces human review and disables auto-merge. This is intentional to prevent unsupervised changes.

**Q: What if the heal PR conflicts with another PR?**
A: GitHub will show a conflict warning. Resolve the conflict manually, or close the heal PR and re-run detect after the other PR is merged.

**Q: Can I run `terraform apply` from this pipeline?**
A: No. The pipeline is designed for formatting only. To apply Terraform changes, use a separate, human-approved workflow (not covered by this pipeline).

---

## Support & Feedback

For issues or questions about this pipeline:
1. Check the Troubleshooting section above.
2. Review GitHub Actions logs for error messages.
3. Open an issue in the repository with details about the failure.

---

**Last updated:** 2026-08-06
**Maintained by:** PoC owners
