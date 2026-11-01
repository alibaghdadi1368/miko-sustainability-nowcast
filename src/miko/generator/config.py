"""Read config/generator.yaml into one object."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from miko.settings import CONFIG_DIR, PROJECT_ROOT


@dataclass(frozen=True)
class Profile:
    name: str
    farms: int
    start: date
    end: date
    gzip: bool = False


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int
    profile: Profile
    truth_dir: Path
    farm: dict[str, Any]
    cow: dict[str, Any]
    feed: dict[str, Any]
    problems: dict[str, Any]
    klw_rules: dict[str, dict[str, Any]]
    reference: dict[str, float]

    def with_profile(self, farms: int, start: str, end: str) -> GeneratorConfig:
        """A copy with another profile. Used by tests."""
        profile = Profile("custom", farms, date.fromisoformat(start), date.fromisoformat(end))
        return replace(self, profile=profile)


def load_generator_config(profile: str = "dev", path: Path | None = None) -> GeneratorConfig:
    path = path or CONFIG_DIR / "generator.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if profile not in raw["profiles"]:
        known = ", ".join(raw["profiles"])
        raise ValueError(f"Unknown profile '{profile}'. Choose one of: {known}")
    p = raw["profiles"][profile]
    start, end = date.fromisoformat(p["start"]), date.fromisoformat(p["end"])
    if end < start:
        raise ValueError(f"Profile '{profile}' ends before it starts")

    return GeneratorConfig(
        seed=int(raw["seed"]),
        profile=Profile(profile, int(p["farms"]), start, end, bool(p.get("gzip", False))),
        truth_dir=PROJECT_ROOT / raw["output"]["truth_dir"],
        farm=raw["farm"],
        cow=raw["cow"],
        feed=raw["feed"],
        problems=raw["problems"],
        klw_rules=raw["klw_rules"],
        reference=raw["reference"],
    )
