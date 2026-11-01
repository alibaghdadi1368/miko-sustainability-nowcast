"""Public dairy formulas (see docs/design.md, section 5.3).

Every function works with one number or with a whole NumPy array of numbers.
"""

from __future__ import annotations

# Protein contains about 16% nitrogen. Milk protein: divide by 6.38, feed protein: by 6.25.
MILK_PROTEIN_TO_N = 6.38
FEED_PROTEIN_TO_N = 6.25
# Ammonia (NH3) weighs 17, the nitrogen (N) in it weighs 14.
NH3_PER_N = 17 / 14


def fpcm(milk_kg, fat_pct, protein_pct):
    """Fat and protein corrected milk (kg), the IDF formula."""
    return milk_kg * (0.1226 * fat_pct + 0.0776 * protein_pct + 0.2534)


def n_milk(milk_kg, protein_pct):
    """Nitrogen in milk (kg)."""
    return milk_kg * protein_pct / 100 / MILK_PROTEIN_TO_N


def n_intake(dm_kg, cp_g_per_kg_dm):
    """Nitrogen eaten with the feed (kg). dm_kg = dry matter in kg."""
    return dm_kg * cp_g_per_kg_dm / 1000 / FEED_PROTEIN_TO_N


def nh3_from_n(n_barn_kg, n_pasture_kg, ef_barn, ef_pasture):
    """Ammonia (kg NH3) from excreted nitrogen in the barn and on pasture."""
    return NH3_PER_N * (n_barn_kg * ef_barn + n_pasture_kg * ef_pasture)
