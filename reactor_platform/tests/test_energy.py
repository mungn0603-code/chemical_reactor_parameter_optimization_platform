"""test_energy.py - CSTR energy balance / heat duty checks."""
from pathlib import Path

import pytest

from reactor_platform.core.energy import (
    EnergyBalance,
    duty_label,
    reaction_heat_rate,
    sensible_heat_rate,
)
from reactor_platform.parameters.registry import ParameterRegistry

CATALOG = (
    Path(__file__).resolve().parents[1] / "parameters" / "catalog" / "energy_example.yaml"
)


def test_component_helpers():
    assert reaction_heat_rate(-80_000.0, 0.32) == pytest.approx(-25_600.0)
    assert sensible_heat_rate(500.0, 353.15, 298.15) == pytest.approx(500.0 * 55.0)


def test_duty_labels():
    assert duty_label(10.0) == "가열"
    assert duty_label(-10.0) == "냉각"
    assert duty_label(0.0) == "단열"


def _reg():
    reg = ParameterRegistry()
    reg.from_yaml(CATALOG)
    return reg


def test_exothermic_reactor_components():
    res = EnergyBalance(_reg()).solve()
    assert res.values["Q_reaction"] < 0
    assert res.values["Q_sensible"] > 0
    assert res.values["Q"] == pytest.approx(
        res.values["Q_reaction"] + res.values["Q_sensible"]
    )
    assert res.ok is True


def test_duty_matches_manual_formula():
    reg = _reg()
    res = EnergyBalance(reg).solve()
    X = res.values["X"]
    v0 = reg.si("v0")
    c_a0 = reg.si("C_A0")
    dH = reg.si("dH_rxn")
    cp = reg.si("cp_flow")
    T = reg.si("temperature")
    T_feed = reg.si("T_feed")
    expected = dH * (v0 * c_a0 * X) + cp * (T - T_feed)
    assert res.values["Q"] == pytest.approx(expected)


def test_report_contains_sections():
    text = EnergyBalance(_reg()).report()
    for token in ["에너지수지", "열부하", "반응열항", "현열항", "판정", "사후 자기검증"]:
        assert token in text
