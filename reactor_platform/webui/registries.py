"""webui/registries.py — 입력값 dict → ParameterRegistry 빌더(UI 전용).

기존 chemical_reactor_app.py 의 배선을 그대로 재사용하되, 진입 파일을 수정하지
않기 위해 UI 계층에 독립 복제한다. 계산 로직/파라미터 스키마는 손대지 않는다.
"""
from __future__ import annotations

from reactor_platform.parameters.registry import ParameterRegistry
from reactor_platform.parameters.schema import Parameter, Role


def _reg(rows: list[tuple]) -> ParameterRegistry:
    reg = ParameterRegistry()
    for key, label, sym, unit, role, desc, val, mn, mx in rows:
        reg.add(Parameter(key, label, sym, unit, role, desc, value=val, min=mn, max=mx))
    return reg


def cstr_energy_registry(v: dict) -> ParameterRegistry:
    """CSTR + 에너지 입력으로 레지스트리를 만든다(M1·M3용)."""
    return _reg([
        ("pre_exponential", "빈도인자", "A", "1/s", Role.INPUT, "빈도인자", v["A"], 0, None),
        ("activation_energy", "활성화에너지", "Ea", "kJ/mol", Role.INPUT, "장벽", v["Ea"], 0, 500),
        ("temperature", "반응온도", "T", "degC", Role.INPUT, "운전온도", v["T"], -273.15, None),
        ("reaction_order", "반응차수", "n", "-", Role.INPUT, "지수", v["n"], 0, 3),
        ("C_A0", "초기농도", "C_A0", "mol/L", Role.INPUT, "입구농도", v["C_A0"], 0, None),
        ("v0", "부피유량", "v0", "L/min", Role.INPUT, "유량", v["v0"], 0, None),
        ("volume", "반응기부피", "V", "L", Role.INPUT, "부피", v["V"], 0, None),
        ("R", "기체상수", "R", "J/mol", Role.CONSTANT, "상수", 8.314462618, None, None),
        ("dH_rxn", "반응열", "dH_rxn", "kJ/mol", Role.INPUT, "반응열", v["dH_rxn"], -5000, 5000),
        ("cp_flow", "열용량유량", "cp_flow", "W/K", Role.INPUT, "현열", v["cp_flow"], 0, None),
        ("T_feed", "공급온도", "T_feed", "degC", Role.INPUT, "공급온도", v["T_feed"], -273.15, None),
        ("k", "속도상수", "k", "1/s", Role.DERIVED, "결과", None, None, None),
        ("tau", "체류시간", "tau", "s", Role.DERIVED, "결과", None, None, None),
        ("X", "전환율", "X", "-", Role.DERIVED, "결과", None, None, None),
        ("Q", "열부하", "Q", "W", Role.DERIVED, "결과", None, None, None),
    ])


def thermo_registry(v: dict) -> ParameterRegistry:
    """열역학 입력으로 레지스트리를 만든다(M2용)."""
    return _reg([
        ("dH", "엔탈피변화", "dH", "kJ/mol", Role.INPUT, "엔탈피", v["dH"], -5000, 5000),
        ("dS", "엔트로피변화", "dS", "J/mol/K", Role.INPUT, "엔트로피", v["dS"], -5000, 5000),
        ("temperature", "반응온도", "T", "degC", Role.INPUT, "온도", v["T"], -273.15, None),
        ("R", "기체상수", "R", "J/mol", Role.CONSTANT, "상수", 8.314462618, None, None),
        ("dG", "자유에너지", "dG", "J/mol", Role.DERIVED, "결과", None, None, None),
        ("K_eq", "평형상수", "K_eq", "-", Role.DERIVED, "결과", None, None, None),
    ])
