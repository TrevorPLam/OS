# ENVIRONMENT.md — Reproducible Dev Environment

Last Updated: 2026-01-02

Goal: prevent environment drift. Pick one approach and record it in `repo.manifest.yaml`.

## Option A: Devcontainer (recommended if you want “it just works”)
Files:
- `.devcontainer/devcontainer.json`
- `.devcontainer/Dockerfile`

How to use:
- Open the repo in a Devcontainer-capable editor.
- Update the Dockerfile if your project needs language runtimes or system deps.

## Option B: Mise / asdf (recommended if you prefer local installs)
Files:
- `mise.toml`
- `.tool-versions`

How to use:
- Install mise or asdf.
- Update the tool versions to match your project.

## Minimal rule
Whichever option you choose, make it the default and keep it consistent across repos.
