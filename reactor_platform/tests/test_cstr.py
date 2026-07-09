"""test_cstr.py — CSTR 전환율: 해석해 대조 + 통합 검증."""
import math

import pytest

from reactor_platform.core.reactors.cstr import _solve_conversion_nth_order
from reactor_platform.core.reactors.cstr import CSTR
from reactor_platform.parameters.registry import ParameterRegistry
from reactor_platform.parameters.schema import Parameter, Role


def analytic_first_order(k, tau):
    return (k * tau) / (1.0 + k * tau)


def analytic_second_order(k, tau, C_A0):
    a = k * C_A0 * tau
    disc = (2 * a + 1) ** 2 - 4 * a * a
    return ((2 * a + 1) - math.sqrt(disc)) / (2 * a)


@pytest.mark.parametrize("k,tau", [(0.01, 10), (0.1, 60), (1.0, 5), (5.0, 120)])
def test_first_order_numeric_matches_analytic(k, tau):
    C_A0 = 1000.0
    X_num = _solve_conversion_nth_order(k, tau, C_A0, 1.0)
    X_exact = analytic_first_order(k, tau)
    assert X_num == pytest.approx(X_exact, abs=1e-6)


@pytest.mark.parametrize("k,tau", [(0.001, 50), (0.01, 60), (0.05, 100)])
def test_second_order_numeric_matches_analytic(k, tau):
    C_A0 = 1000.0
    X_num = _solve_conversion_nth_order(k, tau, C_A0, 2.0)
    X_exact = analytic_second_order(k, tau, C_A0)
    assert X_num == pytest.approx(X_exact, abs=1e-6)


def _build_registry(order=1.0):
    reg = ParameterRegistry()
    defs = [
        ("pre_exponential", "빈도인자", "A", "1/s", Role.INPUT, "빈도인자", 1.0e6, 0, None),
        ("activation_energy", "활성화에너지", "Ea", "J/mol", Role.INPUT, "장벽", 50_000.0, 0, None),
        ("temperature", "온도", "T", "K", Role.INPUT, "절대온도", 353.15, 0, None),
        ("reaction_order", "차수", "n", "-", Role.INPUT, "지수", order, 0, 3),
        ("C_A0", "초기농도", "C_A0", "mol/m^3", Role.INPUT, "입구농도", 1000.0, 0, None),
        ("v0", "유량", "v0", "m^3/s", Role.INPUT, "유량", 1.0e-3, 0, None),
        ("volume", "부피", "V", "m^3", Role.INPUT, "부피", 0.1, 0, None),
        ("R", "기체상수", "R", "J/mol", Role.CONSTANT, "상수", 8.314462618, None, None),
        ("k", "속도상수", "k", "1/s", Role.DERIVED, "결과", None, None, None),
        ("tau", "체류시간", "tau", "s", Role.DERIVED, "결과", None, None, None),
        ("X", "전환율", "X", "-", Role.DERIVED, "결과", None, None, None),
    ]
    for key, label, sym, unit, role, desc, val, mn, mx in defs:
        reg.add(Parameter(key, label, sym, unit, role, desc, value=val, min=mn, max=mx))
    return reg


def test_cstr_solve_first_order_integration():
    reg = _build_registry(order=1.0)
    reactor = CSTR(reg)
    res = reactor.solve()
    assert res.values["tau"] == pytest.approx(100.0)
    k = res.values["k"]
    assert res.values["X"] == pytest.approx(analytic_first_order(k, 100.0), abs=1e-9)
    assert res.ok is True
    assert 0.0 <= res.values["X"] <= 1.0


def test_report_contains_key_sections():
    reg = _build_registry(order=1.0)
    reactor = CSTR(reg)
    text = reactor.report()
    for token in ["계산 리포트", "설명 카드", "Arrhenius", "전환율", "사후 자기검증"]:
        assert token in text
