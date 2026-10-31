"""Load the settings for one environment (local or cloud) from config/<env>.yaml."""

from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
import yaml

# src/miko/settings.py -> parents[0] = miko, [1] = src, [2] = project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"

@dataclass(frozen=True)
class Settings:
    env: str
    landing_dir: Path
    lakehouse_dir: Path
    checkpoint_dir: Path
    spark_driver_memory: str
    spark_shuffle_partitions: int

def load_settings(env: str | None = None) -> Settings:
    """Read config/<env>.yaml. The env comes from the argument, then MIKO_ENV, then 'local'."""
    env = env or os.environ.get("MIKO_ENV", "local")
    path = CONFIG_DIR / f"{env}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No settings file for environment '{env}': {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    paths = raw["paths"]
    spark = raw["spark"]
    return Settings(
        env=raw["env"],
        landing_dir=PROJECT_ROOT / paths["landing"],
        lakehouse_dir=PROJECT_ROOT / paths["lakehouse"],
        checkpoint_dir=PROJECT_ROOT / paths["checkpoints"],
        spark_driver_memory=str(spark["driver_memory"]),
        spark_shuffle_partitions=int(spark["shuffle_partitions"]),
    )