# ADR 0001: Build locally first, with open-source Spark and Delta Lake

- **Status:** accepted
- **Date:** 2026-10-31

## Context

The project should end on Databricks, but learning and iterating in the cloud is slower and
can cost money. The local setup must not become throw-away work.

## Decision

- Develop on Ubuntu (WSL) with **PySpark 4.0** and **open-source Delta Lake 4.0**, in a
  conda environment with Python 3.11 and Java 17 (see ADR 0003).
- Pin `pyspark==4.0.5` and `delta-spark==4.0.1` exactly. `delta-spark` only asks for
  `pyspark>=4.0.0`, so without the pin a newer, incompatible PySpark would be installed.
- Turn **ANSI mode on** (`spark.sql.ansi.enabled=true`), like Spark 4 and Databricks, so a
  bad cast fails loudly instead of becoming NULL.
- All paths and sizes come from `config/<env>.yaml`, never from the code.

## Consequences

- The same transformation code runs locally and on Databricks.
- The first Spark run downloads the Delta jar from Maven Central, so it needs internet.
- Python is fixed to 3.11 (`requires-python = ">=3.11,<3.12"`) for reproducible builds.
