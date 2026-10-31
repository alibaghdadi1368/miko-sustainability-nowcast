# Every common command in one place. Run `make help` to see them.
# Run these inside the conda environment:  conda activate miko
# Recipe lines start with ">" instead of a TAB, so copy-pasting this file cannot break it.
.RECIPEPREFIX = >
.DEFAULT_GOAL := help
.PHONY: help check-env setup lint format test test-fast clean jenkins-up jenkins-down jenkins-logs jenkins-password

help: ## Show this list
> @grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

check-env: ## Show which Python and Java are used (both must come from the miko env)
> @echo "conda env: $${CONDA_DEFAULT_ENV:-none}"
> @which python
> @python --version
> @java -version 2>&1 | head -1

setup: ## Install Miko (editable) with the dev tools, and the git hooks
> python -m pip install -e ".[dev]"
> pre-commit install

lint: ## Check code style (fails if something is wrong)
> ruff check .
> ruff format --check .

format: ## Fix code style automatically
> ruff format .
> ruff check --fix .

test: ## Run all tests
> pytest

test-fast: ## Run only the fast tests (no Spark)
> pytest -m "not spark"

clean: ## Delete generated data and caches
> rm -rf data spark-warehouse metastore_db derby.log reports .pytest_cache .ruff_cache

jenkins-up: ## Build and start Jenkins on http://localhost:8090
> docker compose -f ci/jenkins/docker-compose.yml up -d --build

jenkins-down: ## Stop Jenkins (your jobs and history are kept)
> docker compose -f ci/jenkins/docker-compose.yml down

jenkins-logs: ## Follow the Jenkins log
> docker compose -f ci/jenkins/docker-compose.yml logs -f jenkins

jenkins-password: ## Print the first-login password of Jenkins
> docker compose -f ci/jenkins/docker-compose.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
