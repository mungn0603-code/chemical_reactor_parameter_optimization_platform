"""test_kinetics.py — Arrhenius/속도식 단위 테스트."""
import math

import pytest

from reactor_platform.core.kinetics import arrhenius_k, rate_of_reaction, R_GAS


def test_arrhenius_matches_manual():
    A, Ea, T = 1.0e6, 50_000.0, 353.15
    expected = A * math.exp(-Ea / (R_GAS * T))
    assert arrhenius_k(A, Ea, T) == pytest.approx(expected, rel=1e-12)


def test_arrhenius_increases_with_temperature():
    A, Ea = 1.0e6, 50_000.0
    assert arrhenius_k(A, Ea, 400.0) > arrhenius_k(A, Ea, 300.0)


def test_arrhenius_rejects_nonpositive_temperature():
    with pytest.raises(ValueError):
        arrhenius_k(1.0e6, 50_000.0, 0.0)


def test_rate_first_and_second_order():
    assert rate_of_reaction(2.0, 3.0, 1.0) == pytest.approx(6.0)
    assert rate_of_reaction(2.0, 3.0, 2.0) == pytest.approx(18.0)


def test_rate_rejects_negative_concentration():
    with pytest.raises(ValueError):
        rate_of_reaction(1.0, -1.0, 1.0)
