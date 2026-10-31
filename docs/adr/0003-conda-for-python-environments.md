# ADR 0003: conda for Python and Java, pip for the packages

- **Status:** accepted
- **Date:** 2026-10-31

## Context

The project must install the same versions on my laptop (WSL Ubuntu) and in Jenkins.
I already use Miniconda for my other projects. Spark 4 needs Java 17 or newer, and I do not
want to install Java system-wide with `sudo`.

## Decision

- `environment.yml` creates the `miko` environment with **Python 3.11, OpenJDK 17, make and
  pip**, only from conda-forge (`nodefaults`, so no Anaconda terms-of-service prompt).
- The Python packages are listed in `pyproject.toml` and installed with
  `pip install -e ".[dev]"`. Spark and Delta are pinned exactly (`pyspark==4.0.5`,
  `delta-spark==4.0.1`), because `delta-spark` only asks for `pyspark>=4.0.0`.
- Jenkins uses Miniforge (conda with conda-forge as default) and the same `environment.yml`.

## Consequences

- One file describes the system part (Python, Java), one file describes the packages.
- There is no lock file for indirect dependencies. The packages that matter are pinned; if
  builds start to differ, I will add a lock file (for example with `conda-lock`).
- Every command runs inside `conda activate miko`. `make check-env` shows which Python and
  Java are used.
