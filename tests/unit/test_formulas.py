import numpy as np
import pytest

from miko.domain.formulas import fpcm, n_intake, n_milk, nh3_from_n


def test_fpcm_of_one_kg_standard_milk_is_about_one_kg():
    # Standard milk has 4.0% fat and 3.3% protein: 1 kg of it is 1 kg FPCM.
    assert fpcm(1.0, 4.0, 3.3) == pytest.approx(1.0, abs=0.001)


def test_fpcm_works_on_arrays():
    result = fpcm(np.array([10.0, 20.0]), 4.0, 3.3)
    assert result == pytest.approx([10.0, 20.0], abs=0.01)


def test_nitrogen_in_milk():
    # 30 kg milk with 3.5% protein = 1.05 kg protein = 0.1646 kg N
    assert n_milk(30, 3.5) == pytest.approx(0.1646, abs=0.0001)


def test_nitrogen_intake():
    # 20 kg dry matter with 160 g protein per kg = 3.2 kg protein = 0.512 kg N
    assert n_intake(20, 160) == pytest.approx(0.512)


def test_ammonia_from_nitrogen():
    # 100 kg N in the barn, 13% lost as NH3-N = 13 kg N = 15.79 kg NH3
    assert nh3_from_n(100, 0, 0.13, 0.03) == pytest.approx(15.79, abs=0.01)
