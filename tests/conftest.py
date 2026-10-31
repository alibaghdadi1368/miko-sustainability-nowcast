"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def spark(tmp_path_factory):
    """One Spark session for the whole test run (starting Spark takes a few seconds)."""
    from miko.io.spark import build_spark
    from miko.settings import load_settings

    warehouse = tmp_path_factory.mktemp("warehouse")
    session = build_spark(load_settings("local"), app_name="miko-tests", warehouse_dir=warehouse)
    yield session
    session.stop()
