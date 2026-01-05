# GitHub Actions Parking Lot

All workflows are parked here for cost control. They are **disabled by default**.

## How to enable
1. Copy the desired workflow from `githubactions/workflows/` into `.github/workflows/`.
2. Commit the change and push to run the workflow in GitHub Actions.

## How to disable again
1. Move the workflow file back from `.github/workflows/` to `githubactions/workflows/`.
2. Commit the change to stop future runs.

## Notes
- Each YAML file includes a banner: `# PARKED FOR COST CONTROL — copy to .github/workflows/ to enable`.
- Keep this directory as the source of truth for parked workflows.
- Do not introduce paid CI services without approval.
