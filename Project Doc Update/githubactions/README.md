# githubactions/README.md — GitHub Actions (Disabled by Default)

Status: **OFF (cost control)**
Last Updated: 2026-01-05

This folder stores **GitHub Actions workflows** and related notes **without enabling them**.
Your repo keeps Actions turned off to avoid surprise spend.

## What’s in here
- `githubactions/workflows/` — workflows you can enable later

## Why Actions are off
- Cost control: you’re running a solo, agent-driven workflow and do not want paid automation by default.
- Determinism: local scripts + manual review remain the primary governance mechanism.

## How to enable GitHub Actions (when you choose)
1) Ensure GitHub Actions are enabled in the repository settings.
2) Create `.github/workflows/` (if it doesn’t exist).
3) Copy the workflows from this folder into the live location:

- Copy: `githubactions/workflows/*` → `.github/workflows/`

Example:
```bash
mkdir -p .github/workflows
cp -r githubactions/workflows/* .github/workflows/
git add .github/workflows
git commit -m "Enable GitHub Actions workflows"
```

## How to disable again
Move the workflow files back into `githubactions/workflows/` and remove `.github/workflows/`:
```bash
rm -rf .github/workflows
mkdir -p githubactions/workflows
# (restore files from git history or from your local copies)
```

## Important
- Keeping workflows under `githubactions/` does **not** run anything.
- Nothing in this repo should *require* Actions to make progress.
