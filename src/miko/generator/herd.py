"""Simulate the true life of one farm's herd, day by day. This is the hidden truth.

Every cow has a lactation curve: after calving her milk goes up for about 50 days,
then slowly down. After about 11 months she is dried off for 60 days, then she calves
again. Every day some cows leave the farm; a heifer (young cow) takes their place.

Inside this file a day is a number (date.toordinal()), so "days since calving" is a
simple subtraction for the whole herd at once.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from miko.domain.formulas import fpcm, n_intake, n_milk
from miko.generator.config import GeneratorConfig
from miko.generator.farm import Farm

EPOCH = date(1970, 1, 1).toordinal()
NO_DATE = -1


def to_dates(days) -> pd.Series:
    """Day numbers -> pandas dates. NO_DATE becomes NaT (empty)."""
    days = np.asarray(days, dtype="int64")
    dates = (days - EPOCH).astype("datetime64[D]")
    return pd.Series(np.where(days == NO_DATE, np.datetime64("NaT"), dates))


@dataclass
class SoldCow:
    farm_id: str  # the farm that sold her
    cow_id: str
    birth: int
    lactation_no: int
    exit_day: int


@dataclass
class CowMarket:
    """Cows sold by one farm can be bought by a farm that is simulated later."""

    cows: list[SoldCow] = field(default_factory=list)

    def buy(self, farm_id: str, today: int) -> SoldCow | None:
        for i, cow in enumerate(self.cows):
            if cow.farm_id != farm_id and cow.exit_day < today:
                return self.cows.pop(i)
        return None


@dataclass
class FarmTruth:
    cow_days: pd.DataFrame  # one row per cow per day (milking and dry cows)
    farm_days: pd.DataFrame  # one row per day for the whole farm
    snapshots: pd.DataFrame  # the animal list per day, as the farm software shows it
    moved_cows: list[str]  # cows bought from another farm


def in_grazing_season(day: int, season: list[str]) -> bool:
    return season[0] <= date.fromordinal(day).strftime("%m-%d") <= season[1]


def simulate_herd(
    farm: Farm, cfg: GeneratorConfig, rng: np.random.Generator, market: CowMarket
) -> FarmTruth:
    c, fd = cfg.cow, cfg.feed
    n = farm.herd_size
    first, last = cfg.profile.start.toordinal(), cfg.profile.end.toordinal()
    next_number = 0

    def new_id() -> str:
        nonlocal next_number
        next_number += 1
        return f"NL{farm.number:03d}{next_number:06d}"

    def lactation_length(size=None):
        return np.round(rng.normal(*c["lactation_days"], size)).astype(int)

    # --- The herd on the first day: cows at random points of their cycle.
    lact_no = rng.choice(np.arange(1, 7), size=n, p=c["parity_share"])
    lact_len = lactation_length(n)
    calving = first - (rng.random(n) * (lact_len + c["dry_days"])).astype(int)
    age_at_calving = c["first_calving_age_days"] + (lact_no - 1) * c["calving_interval_days"]
    birth = calving - age_at_calving - rng.integers(0, 60, n)
    cow_id = np.array([new_id() for _ in range(n)], dtype=object)
    potential = rng.lognormal(0, c["potential_sd"], n)
    robot = np.array([f"{farm.farm_id}-R{i % farm.n_robots + 1}" for i in range(n)], dtype=object)

    # Heifers: young stock from 0 to 2 years old. Their number stays the same.
    n_heifers = round(n * farm.youngstock_per_10 / 10)
    heifer_id = np.array([new_id() for _ in range(n_heifers)], dtype=object)
    heifer_birth = first - rng.integers(0, c["first_calving_age_days"], n_heifers)

    cows, herd, farm_rows, moved = defaultdict(list), defaultdict(list), [], []

    def add_animals(day, ids, births, lactations, calvings, status, exit_day=NO_DATE):
        """Add animals to the daily list. A single value (like "heifer") is used for all."""
        size = len(ids)
        values = {
            "day": day,
            "cow_id": ids,
            "birth": births,
            "lactation_no": lactations,
            "calving": calvings,
            "status": status,
            "exit": exit_day,
        }
        for name, value in values.items():
            herd[name].append(np.broadcast_to(np.asarray(value), size).copy())

    exit_prob = c["replacement_rate"] / 365
    farm_factor = 1 + c["skill_milk_effect"] * farm.skill
    wood = c["wood_curve"]

    for day in range(first, last + 1):
        # 1. Cows at the end of their dry period calve again.
        due = day - calving >= lact_len + c["dry_days"]
        calving[due] = day
        lact_no[due] += 1
        lact_len[due] = lactation_length(due.sum())

        # 2. Some cows leave. A bought cow or our oldest heifer takes the place.
        gone = []
        for i in np.flatnonzero(rng.random(n) < exit_prob):
            gone.append((cow_id[i], birth[i], lact_no[i], calving[i]))
            if rng.random() < c["sold_share"]:
                market.cows.append(
                    SoldCow(farm.farm_id, cow_id[i], int(birth[i]), int(lact_no[i]), day)
                )
            bought = (
                market.buy(farm.farm_id, day)
                if rng.random() < cfg.problems["cow_move_share"]
                else None
            )
            if bought:
                newcomer = (bought.cow_id, bought.birth, bought.lactation_no + 1)
                moved.append(bought.cow_id)
            else:
                oldest = int(np.argmin(heifer_birth))
                newcomer = (heifer_id[oldest], heifer_birth[oldest], 1)
                heifer_id[oldest], heifer_birth[oldest] = new_id(), day  # a calf is born
            cow_id[i], birth[i], lact_no[i] = newcomer
            calving[i], lact_len[i] = day, lactation_length()
            potential[i] = rng.lognormal(0, c["potential_sd"])

        # 3. Milk, feed and nitrogen of today.
        dim = day - calving  # days in milk
        milking = dim < lact_len
        t = dim + 1
        curve = wood["a"] * t ** wood["b"] * np.exp(-wood["c"] * t)
        curve = curve * np.where(lact_no == 1, c["first_lactation_factor"], 1.0)
        milk = curve * potential * farm_factor * rng.lognormal(0, c["day_noise_sd"], n)
        milk = np.where(milking, milk, 0.0)
        fat = c["fat_pct"][0] + c["fat_pct"][1] * (28 - curve) + rng.normal(0, c["fat_pct"][2], n)
        protein = (
            c["protein_pct"][0]
            + c["protein_pct"][1] * (28 - curve)
            + rng.normal(0, c["protein_pct"][2], n)
        )
        lactose = rng.normal(*c["lactose_pct"], n)

        grazing = 0.0
        if farm.grazing_hours > 0 and in_grazing_season(day, cfg.farm["grazing_season"]):
            weather = 0.0 if rng.random() < 0.1 else rng.uniform(0.6, 1.1)  # rainy days: inside
            grazing = round(farm.grazing_hours * weather, 1)

        efficiency = 1 - fd["skill_efficiency"] * farm.skill
        dmi_milking = (
            fd["dmi_base"] + fd["dmi_per_kg_fpcm"] * fpcm(milk, fat, protein)
        ) * efficiency
        dmi = np.where(milking, dmi_milking, fd["dmi_dry"])
        slope, offset, low, high = fd["concentrate"]
        conc = np.where(milking, np.clip(slope * milk - offset, low, high), 0.0)
        conc_dm = conc * fd["concentrate_dm"]
        ration_cp = (
            farm.ration_cp + fd["grass_cp_bonus"] * grazing / 8 + rng.normal(0, fd["cp_day_sd"])
        )
        roughage_cp = np.where(milking, ration_cp, fd["dry_ration_cp"])
        n_in = n_intake(conc_dm, fd["concentrate_cp"]) + n_intake(dmi - conc_dm, roughage_cp)
        n_out = n_milk(milk, protein)
        retained = np.where(milking, fd["n_retained_lactating"], fd["n_retained_dry"])

        for name, values in {
            "day": np.full(n, day),
            "cow_id": cow_id.copy(),
            "robot_id": robot,
            "milking": milking,
            "lactation_no": lact_no.copy(),
            "dim": dim,
            "milk_kg": milk,
            "fat_pct": fat,
            "protein_pct": protein,
            "lactose_pct": lactose,
            "concentrate_kg": conc,
            "dmi_kg": dmi,
            "roughage_dm_kg": dmi - conc_dm,
            "grazing_h": np.where(milking, grazing, 0.0),
            "n_intake_kg": n_in,
            "n_milk_kg": n_out,
            "n_excreted_kg": n_in - n_out - retained,
        }.items():
            cows[name].append(values)
        farm_rows.append(
            {"day": day, "ration_cp": ration_cp, "grazing_h": grazing, "heifers": n_heifers}
        )

        # 4. Today's animal list (source S6): cows, heifers, and cows that left today.
        add_animals(day, cow_id, birth, lact_no, calving, np.where(milking, "milking", "dry"))
        add_animals(day, heifer_id, heifer_birth, 0, NO_DATE, "heifer")
        if gone:
            ids, births, lactations, calvings = zip(*gone, strict=True)
            add_animals(day, ids, births, lactations, calvings, "exited", exit_day=day)

    cow_days = pd.DataFrame({name: np.concatenate(parts) for name, parts in cows.items()})
    cow_days.insert(0, "date", to_dates(cow_days.pop("day")))
    farm_days = pd.DataFrame(farm_rows)
    farm_days.insert(0, "date", to_dates(farm_days.pop("day")))

    h = {name: np.concatenate(parts) for name, parts in herd.items()}
    group = {"milking": "LACT", "dry": "DRY", "heifer": "YOUNG", "exited": ""}  # "" = no group
    snapshots = pd.DataFrame(
        {
            "snapshot_date": to_dates(h["day"]),
            "cow_id": h["cow_id"],
            "birth_date": to_dates(h["birth"]),
            "lactation_no": h["lactation_no"].astype(int),
            "calving_date": to_dates(h["calving"]),
            "group_id": pd.Series(h["status"]).map(group),
            "status": h["status"],
            "exit_date": to_dates(h["exit"]),
        }
    )
    return FarmTruth(cow_days, farm_days, snapshots, moved)
