# Miko: sustainability nowcast for dairy farms

> **Know your farm's footprint before the year is over.**

Dutch dairy farmers get their environmental results (the *KringloopWijzer*) once a year,
months after the year has ended. **Miko** uses the daily data from milking and feeding robots
to estimate those results **now**, forecast where the farm will end up by December, and
suggest one or two simple actions.

*Bayal Dairy Robotics is a fictional company, named after the village in Dariush Mehrjui's
film* The Cow *(1969). Miko is named after my cat. All data in this project is synthetic.*

**Stack:** Python · PySpark · Delta Lake · MLflow · Streamlit · Jenkins · Docker ·
Databricks · Unity Catalog · Terraform



---

## Project status

Each phase ends with something that runs. Ticked boxes are done.

### Phase 0 · Foundations
- [x] Repository, folder structure, `.gitignore`, licence
- [x] conda environment (`environment.yml`) and Python package (`pyproject.toml`)
- [x] Settings per environment (`config/local.yaml`)
- [x] Spark 4 + Delta Lake session, ANSI mode on
- [x] "Hello Delta" tests: write, append, time travel, MERGE, idempotency
- [ ] Code quality: `ruff` + `pre-commit`
- [x] `Makefile` for every common command
- [ ] Jenkins in Docker with a `Jenkinsfile` (lint → unit tests → Spark tests)
- [ ] Design document and first decision records (ADRs)

### Phase 1 · Synthetic data generator
- [ ] Cow and farm simulation with hidden factors
- [ ] Robot, feed, collar, herd and tank-milk sources
- [ ] KLW reference engine and XML writer, two rule versions
- [ ] Planned data problems (duplicates, late data, wrong units, ...)
- [ ] `tiny` / `dev` / `full` profiles, validated against Dutch averages

### Phase 2 · Bronze
- [ ] Incremental ingestion with Structured Streaming (`availableNow`)
- [ ] Ingest metadata, rescued data, bad-file handling

### Phase 3 · Silver
- [ ] Deduplication and late data with MERGE
- [ ] `dim_cow` and `dim_farm` as SCD2 from CDC snapshots
- [ ] Version-aware KLW XML parser and `dim_rekenregels`
- [ ] Data quality framework and quarantine

### Phase 4 · Gold (MVP)
- [ ] Daily and monthly indicators (FPCM, nitrogen, ammonia, greenhouse gases)
- [ ] Anonymous benchmark (groups of 5 farms or more)
- [ ] Data quality scorecard and consent views

### Phase 5 · Nowcast model
- [ ] As-of feature table without data leakage
- [ ] Baselines and hybrid model with p10 / p50 / p90
- [ ] Backtest, MLflow tracking, model card

### Phase 6 · Advice and what-if
- [ ] Rule-based advice with estimated effect and confidence
- [ ] What-if scenarios with guardrails

### Phase 7 · Dashboard (local v1)
- [ ] Farmer, what-if and advisor pages in Streamlit, offline

### Phase 8 · Cloud
- [ ] Databricks: Unity Catalog, Auto Loader, Workflows, Asset Bundles
- [ ] Terraform, row filters and column masks, deploy from Jenkins

### Phase 9 · Launch (v1.0)
- [ ] Final README, results, demo video

---

## Run it locally

You need Ubuntu (or WSL) and Miniconda. Java 17 and `make` come from the conda environment.

```bash
conda env create -f environment.yml   # once: Python 3.11, Java 17, make
conda activate miko
make setup   # install Miko and the dev tools, install the git hooks
make lint    # ruff
make test    # all tests (the first Spark run downloads the Delta jar)
```

## Licence

MIT, see [LICENSE](LICENSE).
