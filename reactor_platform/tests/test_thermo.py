"""test_thermo.py - thermodynamic feasibility: formula + verdict checks."""
import math
from pathlib import Path

import pytest

from reactor_platform.core.thermo import (
    ThermoAnalyzer,
    equilibrium_constant,
    gibbs_free_energy,
    spontaneity_label,
)
from reactor_platform.parameters.registry import ParameterRegistry
from reactor_platform.parameters.schema import Parameter, Role

CATALOG = (
    Path(__file__).resolve().parents[1] / "parameters" / "catalog" / "thermo_example.yaml"
)
R = 8.314462618


def test_gibbs_matches_manual():
    assert gibbs_free_energy(-50_000.0, 80.0, 353.15) == pytest.approx(
        -50_000.0 - 353.15 * 80.0
    )


def test_keq_matches_manual():
    dG = -78_252.0
    assert equilibrium_constant(dG, 353.15, R) == pytest.approx(
        math.exp(-dG / (R * 353.15))
    )


def test_spontaneity_labels():
    assert spontaneity_label(-1.0) == "자발적"
    assert spontaneity_label(1.0) == "비자발적"
    assert spontaneity_label(0.0) == "평형"


def test_gibbs_rejects_nonpositive_temperature():
    with pytest.raises(ValueError):
        gibbs_free_energy(-50_000.0, 80.0, 0.0)


def _build_registry(dH_J=-50_000.0, dS=80.0, T=353.15):
    reg = ParameterRegistry()
    defs = [
        ("dH", "엔탈피", "dH", "J/mol", Role.INPUT, "엔탈피 변화", dH_J),
        ("dS", "엔트로피", "dS", "J/mol/K", Role.INPUT, "엔트로피 변화", dS),
        ("temperature", "온도", "T", "K", Role.INPUT, "절대온도", T),
        ("R", "기체상수", "R", "J/mol", Role.CONSTANT, "상수", R),
        ("dG", "자유에너지", "dG", "J/mol", Role.DERIVED, "결과", None),
        ("K_eq", "평형상수", "K_eq", "-", Role.DERIVED, "결과", None),
    ]
    for key, label, sym, unit, role, desc, val in defs:
        reg.add(Parameter(key, label, sym, unit, role, desc, value=val))
    return reg


def test_exothermic_entropy_up_is_spontaneous():
    res = ThermoAnalyzer(_build_registry()).solve()
    assert res.values["dG"] < 0
    assert res.verdict == "자발적"
    assert res.values["K_eq"] > 1
    assert res.ok is True


def test_endothermic_entropy_down_is_nonspontaneous():
    res = ThermoAnalyzer(_build_registry(dH_J=50_000.0, dS=-80.0)).solve()
    assert res.values["dG"] > 0
    assert res.verdict == "비자발적"
    assert res.values["K_eq"] < 1


def test_catalog_solves_and_reports():
    reg = ParameterRegistry()
    reg.from_yaml(CATALOG)
    analyzer = ThermoAnalyzer(reg)
    text = analyzer.report()
    for token in ["열역학", "dG", "K_eq", "판정", "사후 자기검증"]:
        assert token in text
