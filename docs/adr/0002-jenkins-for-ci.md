# ADR 0002: Jenkins for continuous integration

- **Status:** accepted
- **Date:** 2026-10-31

## Context

The project needs CI: lint and tests on every change. GitHub Actions is the simplest choice,
but Jenkins is still widely used by Dutch companies, and learning it is part of the goal.

## Decision

- Run **Jenkins in Docker** on the development machine (`ci/jenkins/`), on port 8090.
- Keep the pipeline in the repository as a declarative **`Jenkinsfile`**:
  Setup (conda env from `environment.yml`) → Lint (ruff) → Unit tests → Spark tests, with JUnit reports.
- Use a **Multibranch Pipeline** job that polls the public GitHub repository, so every
  branch (for example `phase-0-foundations`) is tested before it is merged.

## Consequences

- No webhook: Jenkins runs locally and cannot be reached from GitHub, so it **polls** for
  new commits every few minutes.
- No public CI badge on GitHub. The README links to this decision instead.
- Jenkins must be running (`make jenkins-up`) to test a branch.
- In Phase 8 the same Jenkinsfile gets a deploy stage for Databricks Asset Bundles.
