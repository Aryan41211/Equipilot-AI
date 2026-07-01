# GitHub Workflow Documentation

This document describes how we collaborate on EquiPilot AI via GitHub.

## Branch strategy
- Use feature branches off the repository’s default branch.
- Branch naming:
  - `feature/<short-description>`
  - `fix/<short-description>`
  - `chore/<short-description>`
- Keep branches focused on a single logical change per PR.

## Pull request workflow
1. Create a branch and implement changes.
2. Update documentation if user-facing behavior or APIs are affected.
3. Ensure formatting and lint checks pass (Ruff/Black) and tests are added/updated as needed.
4. Open a pull request targeting the default branch.
5. Provide:
   - A clear summary of what changed
   - The motivation for changes
   - Testing performed
   - Any relevant screenshots/logs (no secrets)

### Code review expectations
- Reviewers will focus on correctness, maintainability, and consistency with project standards.
- Changes should not duplicate existing patterns or documentation unless necessary.
- If behavior changes are made, they must be explained clearly (and should be limited to the intent of the PR).

## Release workflow
- Releases are created by maintainers after:
  - CI passes
  - Changes are reviewed and merged
  - Versioning is updated (if applicable)
- Changelog updates (if used) should be included as part of the release PR.
