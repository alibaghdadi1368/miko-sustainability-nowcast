"""Turn the hidden truth into the data that devices and companies send (sources S1 to S9).

Each function returns a pandas DataFrame with exactly the columns of one source.
Times are UTC text like 2025-03-01T05:12:33Z.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from miko.generator.config import GeneratorConfig
from miko.generator.farm import Farm
from miko.generator.herd import FarmTruth

DAY_SECONDS = 86_400


def to_utc_text(seconds) -> np.ndarray:
    """Seconds since 1970 (UTC) -> '2025-03-01T05:12:33Z'. NumPy does this fast."""
    as_time = np.asarray(seconds, dtype="int64").astype("datetime64[s]")
    return np.char.add(np.datetime_as_string(as_time, unit="s"), "Z")


def day_start_seconds(days) -> np.ndarray:
    """Dates -> seconds since 1970 at 00:00 UTC."""
    return np.asarray(days, dtype="datetime64[s]").astype("int64")


def milking_events(farm: Farm, truth: FarmTruth, rng: np.random.Generator) -> pd.DataFrame:
    """S1: one row per robot visit. A cow visits the robot 2 to 4 times a day."""
    cows = truth.cow_days[truth.cow_days["milking"]].reset_index(drop=True)
    noise = rng.normal(0, 0.6, len(cows))
    visits = np.clip(np.round(0.8 + cows["milk_kg"].to_numpy() / 14 + noise), 2, 4).astype(int)
    cow_day = np.repeat(np.arange(len(cows)), visits)  # [0, 0, 1, 1, 1, ...]
    ev = cows.iloc[cow_day].reset_index(drop=True)
    ev["visits"] = visits[cow_day]
    ev["k"] = np.arange(len(ev)) - np.repeat(np.cumsum(visits) - visits, visits)  # 0, 1, 0, 1, 2

    # Split the day's milk over the visits, and spread the visits over the day.
    share = rng.gamma(8, size=len(ev))
    share = share / np.bincount(cow_day, weights=share)[cow_day]
    gap = DAY_SECONDS / ev["visits"]
    offset = rng.uniform(0, 0.7, len(cows))[cow_day] * gap
    second = offset + ev["k"] * gap + rng.uniform(0, 0.3, len(ev)) * gap
    second = np.minimum(second, DAY_SECONDS - 600).astype(int)
    start = day_start_seconds(ev["date"]) + second
    end = start + rng.integers(360, 540, len(ev))

    out = pd.DataFrame(
        {
            "farm_id": farm.farm_id,
            "cow_id": ev["cow_id"],
            "robot_id": ev["robot_id"],
            "start_s": start,
            "end_s": end,
            "sent_s": end + rng.exponential(20, len(ev)).astype(int) + 1,
            "milk_kg": (ev["milk_kg"] * share).round(2),
            "fat_pct": (ev["fat_pct"] + rng.normal(0, 0.1, len(ev))).round(2),
            "protein_pct": (ev["protein_pct"] + rng.normal(0, 0.04, len(ev))).round(2),
            "lactose_pct": (ev["lactose_pct"] + rng.normal(0, 0.03, len(ev))).round(2),
            "conductivity_ms_cm": rng.normal(4.9, 0.3, len(ev)).round(2),
            "milk_temp_c": rng.normal(37.6, 0.3, len(ev)).round(1),
            "concentrate_kg": (ev["concentrate_kg"] / ev["visits"]).round(2),
        }
    )
    # The robot numbers its own events: R1-00000001, R1-00000002, ...
    out = out.sort_values(["robot_id", "start_s"], kind="stable").reset_index(drop=True)
    seq = out.groupby("robot_id").cumcount() + 1
    out.insert(0, "event_id", out["robot_id"] + "-" + seq.map("{:08d}".format))
    return out


def feed_events(farm: Farm, truth: FarmTruth, rng: np.random.Generator) -> pd.DataFrame:
    """S2: one row per delivery of the feeding robot. Empty if the farm has no feeder."""
    columns = [
        "event_id",
        "farm_id",
        "group_id",
        "ration_id",
        "timestamp_s",
        "fed_kg_fresh",
        "refusal_kg",
    ]
    if not farm.has_feeder:
        return pd.DataFrame(columns=columns)

    per_group = truth.cow_days.groupby(["date", "milking"])["roughage_dm_kg"].sum().reset_index()
    schedule = {True: ("LACT", [5, 8, 11, 14, 17, 21]), False: ("DRY", [7, 16])}
    rows = []
    for row in per_group.itertuples():
        group, hours = schedule[row.milking]
        midnight = int(day_start_seconds([row.date])[0])
        refusal = rng.uniform(0.02, 0.06)
        fresh_per_delivery = (
            row.roughage_dm_kg / (farm.ration_dm_pct / 100) * (1 + refusal) / len(hours)
        )
        for hour in hours:
            fed = fresh_per_delivery * rng.normal(1, 0.05)
            rows.append(
                {
                    "group_id": group,
                    "ration_id": f"{farm.farm_id}-{group}",
                    "timestamp_s": midnight + hour * 3600 + int(rng.integers(0, 900)),
                    "fed_kg_fresh": round(fed, 1),
                    "refusal_kg": round(fed * refusal, 1),
                }
            )
    out = pd.DataFrame(rows).sort_values("timestamp_s", kind="stable").reset_index(drop=True)
    out.insert(0, "farm_id", farm.farm_id)
    out.insert(0, "event_id", [f"{farm.farm_id}-F-{i:07d}" for i in range(1, len(out) + 1)])
    return out[columns]


def feed_analyses(
    farm: Farm, truth: FarmTruth, cfg: GeneratorConfig, rng: np.random.Generator
) -> pd.DataFrame:
    """S3: lab analysis of each ration, about every 75 days."""
    fd = truth.farm_days.set_index("date")
    rows = []
    for group in ("LACT", "DRY"):
        day = cfg.profile.start + timedelta(days=int(rng.integers(0, 20)))
        while day <= cfg.profile.end:
            true_cp = (
                fd.loc[pd.Timestamp(day), "ration_cp"]
                if group == "LACT"
                else cfg.feed["dry_ration_cp"]
            )
            rows.append(
                {
                    "ration_id": f"{farm.farm_id}-{group}",
                    "farm_id": farm.farm_id,
                    "sample_date": day.isoformat(),
                    "dm_pct": round(farm.ration_dm_pct + rng.normal(0, 1.5), 1),
                    "cp_g_per_kg_dm": round(true_cp + rng.normal(0, 4)),
                    "vem_per_kg_dm": round(rng.normal(950 if group == "LACT" else 850, 25)),
                    "ndf_g_per_kg_dm": round(rng.normal(400 if group == "LACT" else 500, 20)),
                }
            )
            day += timedelta(days=int(rng.integers(60, 91)))
    return pd.DataFrame(rows)


def tank_milk(
    farm: Farm, truth: FarmTruth, cfg: GeneratorConfig, rng: np.random.Generator
) -> pd.DataFrame:
    """S4: the dairy company collects the milk every 3 days and analyses it."""
    fd = cfg.feed
    cd = truth.cow_days
    daily = cd.assign(
        fat_kg=cd["milk_kg"] * cd["fat_pct"] / 100,
        protein_kg=cd["milk_kg"] * cd["protein_pct"] / 100,
    )
    daily = daily.groupby("date")[
        ["milk_kg", "fat_kg", "protein_kg", "n_intake_kg", "dmi_kg"]
    ].sum()
    pickup = np.arange(len(daily)) // 3
    rows = []
    for _, part in daily.groupby(pickup):
        if len(part) < 3:  # the last pickup is not complete yet
            break
        milk = part["milk_kg"].sum()
        cp = part["n_intake_kg"].sum() * 6250 / part["dmi_kg"].sum()  # crude protein of all feed
        urea = fd["urea"][0] + fd["urea"][1] * (cp - 160) + rng.normal(0, fd["urea"][2])
        rows.append(
            {
                "farm_id": farm.farm_id,
                "pickup_date": part.index[-1].strftime("%Y-%m-%d"),
                "litres": round(milk * fd["delivered_share"] / 1.03),
                "fat_pct": round(part["fat_kg"].sum() / milk * 100 + rng.normal(0, 0.03), 2),
                "protein_pct": round(
                    part["protein_kg"].sum() / milk * 100 + rng.normal(0, 0.02), 2
                ),
                "urea_mg_100g": round(urea, 1),
                "scc_x1000_per_ml": round(rng.lognormal(np.log(180 - 20 * farm.skill), 0.25)),
            }
        )
    return pd.DataFrame(rows)


def collar_daily(farm: Farm, truth: FarmTruth, rng: np.random.Generator) -> pd.DataFrame:
    """S5: the collar counts minutes per cow per day."""
    cd = truth.cow_days
    n = len(cd)
    rumination = rng.normal(500, 40, n) - np.where(cd["milking"], 0, 50)
    rumination -= np.where(cd["dim"] < 10, 80, 0)  # fresh cows ruminate less
    activity = rng.normal(100, 15, n) + np.where(rng.random(n) < 0.02, 80, 0)  # in heat
    return pd.DataFrame(
        {
            "farm_id": farm.farm_id,
            "cow_id": cd["cow_id"],
            "date": cd["date"].dt.strftime("%Y-%m-%d"),
            "rumination_min": rumination.round().astype(int),
            "activity_index": activity.round().astype(int),
            "grazing_min": (cd["grazing_h"] * 60 * rng.uniform(0.85, 1.05, n)).round().astype(int),
        }
    )


def herd_snapshots(farm: Farm, truth: FarmTruth) -> pd.DataFrame:
    """S6: the farm software exports the full animal list every day."""
    s = truth.snapshots.copy()
    for col in ("snapshot_date", "birth_date", "calving_date", "exit_date"):
        s[col] = s[col].dt.strftime("%Y-%m-%d").fillna("")
    s.insert(0, "farm_id", farm.farm_id)
    return s


def farm_master(farms: list[Farm], day: date) -> pd.DataFrame:
    """S7: master data of all farms, as known on one day."""
    return pd.DataFrame(
        [
            {
                "farm_id": f.farm_id,
                "region": f.region,
                "soil_type": f.soil_type,
                "area_ha": f.area_ha[day.year],
                "grassland_ha": round(f.grassland_ha(day.year), 1),
                "maize_ha": round(f.maize_ha(day.year), 1),
                "n_robots": f.n_robots,
                "has_feeder": f.has_feeder,
            }
            for f in farms
        ]
    )


def consents(farms: list[Farm], cfg: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    """S9: who may use the data of a farm, for what, and from when to when."""
    start, end = cfg.profile.start, cfg.profile.end
    span = (end - start).days + 1
    rows = []
    for f in farms:
        rows.append((f.farm_id, "bayal-miko", "nowcast", start.isoformat(), ""))
        if rng.random() < 0.7:
            rows.append((f.farm_id, "bayal-benchmark", "benchmark", start.isoformat(), ""))
        if rng.random() < 0.4:
            begin = start + timedelta(days=int(rng.integers(0, span)))
            stop = ""
            if rng.random() < 0.25:  # the farmer withdrew this consent later
                stop = min(end, begin + timedelta(days=int(rng.integers(30, 365)))).isoformat()
            advisor = f"advisor-{int(rng.integers(1, 6)):02d}"
            rows.append((f.farm_id, advisor, "advice", begin.isoformat(), stop))
    return pd.DataFrame(rows, columns=["farm_id", "grantee", "purpose", "valid_from", "valid_to"])
