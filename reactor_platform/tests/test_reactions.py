"""test_reactions.py — 반응식 파싱·원소균형·표준 반응 열역학(교과서 값) 검증.

기준값 출처: NIST / CRC / Smith·Van Ness·Abbott 부록 C 의 통용 표준값(298.15 K).
계산이 Hess 의 법칙을 정확히 따르는지, 교과서 값에 근접하는지 확인한다.
"""
import math

import pytest

from reactor_platform.core.reactions import (
    REACTION_LIBRARY,
    ReactionError,
    analyze_reaction,
    element_balance,
    parse_formula,
    parse_reaction,
    reaction_thermochemistry,
)


def test_parse_formula_counts_elements():
    assert parse_formula("C2H6O") == {"C": 2, "H": 6, "O": 1}
    assert parse_formula("H2O") == {"H": 2, "O": 1}
    assert parse_formula("CO2") == {"C": 1, "O": 2}


def test_parse_reaction_coefficients_and_arrow():
    rxn = parse_reaction("N2 + 3 H2 -> 2 NH3")
    assert len(rxn.reactants) == 2 and len(rxn.products) == 1
    coeff, sp = rxn.products[0]
    assert coeff == 2.0 and sp.key == "NH3"


def test_missing_arrow_raises():
    with pytest.raises(ReactionError):
        parse_reaction("N2 + 3 H2 2 NH3")


def test_unknown_species_raises():
    with pytest.raises(ReactionError):
        parse_reaction("N2 + Xx -> Yy")


def test_haber_is_element_balanced():
    ok, residual = element_balance(parse_reaction("N2 + 3 H2 -> 2 NH3"))
    assert ok and residual == {}


def test_unbalanced_detected():
    # 원소가 맞지 않는 반응은 balanced=False.
    ok, residual = element_balance(parse_reaction("N2 + H2 -> NH3"))
    assert not ok and residual


def test_haber_enthalpy_matches_textbook():
    r = analyze_reaction("N2 + 3 H2 -> 2 NH3", T=298.15)
    # 교과서 ΔH° ≈ -92 kJ/mol, ΔS° < 0 (기체 몰수 감소).
    assert r.dH_rxn == pytest.approx(-91.8, abs=1.5)
    assert r.dS_rxn < 0
    assert r.enthalpy_label.startswith("발열")


def test_methane_combustion_matches_textbook():
    r = analyze_reaction("CH4 + 2 O2 -> CO2 + 2 H2O(g)")
    # 교과서 연소열(기체 물) ΔH° ≈ -802 kJ/mol.
    assert r.dH_rxn == pytest.approx(-802.3, abs=2.0)


def test_liquid_water_gives_higher_heating_value():
    gas = analyze_reaction("CH4 + 2 O2 -> CO2 + 2 H2O(g)").dH_rxn
    liq = analyze_reaction("CH4 + 2 O2 -> CO2 + 2 H2O(l)").dH_rxn
    # 액체 물 생성(HHV)이 더 큰 발열(더 음수).
    assert liq < gas
    assert liq == pytest.approx(-890.4, abs=2.0)


def test_endothermic_reaction_is_nonspontaneous_at_298():
    r = analyze_reaction("N2 + O2 -> 2 NO", T=298.15)
    assert r.dH_rxn > 0  # 흡열
    assert r.dG_rxn > 0  # 298K 비자발적
    assert r.spontaneity_label == "비자발적"
    assert r.K_eq < 1.0


def test_gibbs_temperature_dependence():
    # ΔG = ΔH - T·ΔS. 발열·ΔS<0 반응은 온도가 오르면 ΔG 가 증가(덜 자발적).
    low = analyze_reaction("N2 + 3 H2 -> 2 NH3", T=300.0).dG_rxn
    high = analyze_reaction("N2 + 3 H2 -> 2 NH3", T=800.0).dG_rxn
    assert high > low


def test_keq_formula_consistency():
    r = analyze_reaction("CO + H2O(g) -> CO2 + H2", T=500.0)
    expected = math.exp(-(r.dG_rxn * 1000.0) / (8.314462618 * 500.0))
    assert r.K_eq == pytest.approx(expected, rel=1e-9)


def test_safe_exp_no_overflow_for_large_reaction():
    # 포도당 완전연소는 ΔG 가 매우 커 K_eq 가 오버플로 없이 inf 로 처리돼야 한다.
    r = analyze_reaction("C6H12O6(s) + 6 O2 -> 6 CO2 + 6 H2O(l)")
    assert r.dH_rxn < 0
    assert math.isinf(r.K_eq) or r.K_eq > 0


def test_zero_temperature_raises():
    with pytest.raises(ReactionError):
        reaction_thermochemistry(parse_reaction("N2 + 3 H2 -> 2 NH3"), T=0.0)


@pytest.mark.parametrize("named", REACTION_LIBRARY, ids=lambda n: n.name)
def test_library_reactions_parse_and_balance(named):
    r = analyze_reaction(named.equation)
    ok, residual = element_balance(r.reaction)
    assert ok, f"{named.name} 불균형: {residual}"
    assert r.steps  # 유도 과정이 기록됨
