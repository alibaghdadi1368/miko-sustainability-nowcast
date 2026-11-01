"""Create the farms: what the farm software knows, plus hidden factors that only the
simulator knows (management skill, fertiliser, ...)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from miko.generator.config import GeneratorConfig

# Where each soil type is common in the Netherlands (simplified).
REGIONS = {
    "sand": ["Gelderland", "Overijssel", "Noord-Brabant", "Drenthe"],
    "clay": ["Friesland", "Groningen", "Noord-Holland", "Zeeland"],
    "peat": ["Utrecht", "Zuid-Holland", "Noord-Holland", "Friesland"],
}


@dataclass
class Farm:
    farm_id: str
    number: int
    region: str
    soil_type: str
    herd_size: int
    area_ha: dict[int, float]  # area per year (it can change)
    grassland_share: float
    has_feeder: bool
    n_robots: int
    # Hidden factors: never written to the landing zone.
    skill: float  # management skill, around 0 (bad < 0 < good)
    ration_cp: float  # crude protein of the basic ration, g/kg DM
    ration_dm_pct: float
    grazing_hours: float  # 0 = cows stay inside all year
    youngstock_per_10: float
    fertiliser_n_per_ha: float
    manure_export_share: float
    drift_robot: int | None  # index of the robot with a wrong clock, or None

    def grassland_ha(self, year: int) -> float:
        return self.area_ha[year] * self.grassland_share

    def maize_ha(self, year: int) -> float:
        return self.area_ha[year] - self.grassland_ha(year)


def make_farm(number: int, cfg: GeneratorConfig, rng: np.random.Generator) -> Farm:
    f = cfg.farm
    soils = list(f["soil_share"])
    soil = str(rng.choice(soils, p=[f["soil_share"][s] for s in soils]))
    herd = int(rng.integers(f["herd_size"][0], f["herd_size"][1] + 1))
    skill = float(np.clip(rng.normal(0, 1), -2, 2))
    n_robots = math.ceil(herd / f["cows_per_robot"])

    # Area per year: some farms buy or sell land at the start of a new year.
    first, last = cfg.profile.start.year, cfg.profile.end.year
    area = {first: round(herd / rng.uniform(*f["cows_per_ha"]), 1)}
    for year in range(first + 1, last + 1):
        change = rng.uniform(0.9, 1.15) if rng.random() < f["area_change_share"] else 1.0
        area[year] = round(area[year - 1] * change, 1)

    grazes = rng.random() < f["grazing_share"]
    drift = rng.random() < cfg.problems["clock_drift_share"]
    return Farm(
        farm_id=f"FARM-{number:04d}",
        number=number,
        region=str(rng.choice(REGIONS[soil])),
        soil_type=soil,
        herd_size=herd,
        area_ha=area,
        grassland_share=round(rng.uniform(*f["grassland_share"]), 2),
        has_feeder=bool(rng.random() < f["feeder_share"]),
        n_robots=n_robots,
        skill=round(skill, 3),
        # Good managers feed less protein: -4 g/kg DM per point of skill.
        ration_cp=round(rng.uniform(*f["ration_cp"]) - 4 * skill, 1),
        ration_dm_pct=round(rng.uniform(*cfg.feed["ration_dm_pct"]), 1),
        grazing_hours=round(rng.uniform(*f["grazing_hours"]), 1) if grazes else 0.0,
        youngstock_per_10=round(rng.uniform(*f["youngstock_per_10_cows"]), 2),
        fertiliser_n_per_ha=round(rng.uniform(*f["fertiliser_n_per_ha"]), 1),
        manure_export_share=round(rng.uniform(*f["manure_export_share"]), 3),
        drift_robot=int(rng.integers(n_robots)) if drift else None,
    )
