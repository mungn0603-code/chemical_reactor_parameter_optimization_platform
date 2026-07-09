"""core/units.py — 단위계: SI 고정 + 경계 변환.

내부 계산은 전부 SI 단위로만 수행하고, 사용자 단위는 '입력 경계'에서
딱 한 번 SI로 변환한다. 각 단위는 (차원, 배율 factor, 오프셋 offset) 로 정의된다.
SI 값 = value * factor + offset.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnitError(ValueError):
    """단위 관련 오류(미등록 단위, 차원 불일치 등)."""


@dataclass(frozen=True)
class UnitDef:
    """하나의 단위 정의(차원, SI 배율, 오프셋, SI 기준 단위)."""

    dimension: str
    factor: float
    offset: float
    si_unit: str


_UNITS: dict[str, UnitDef] = {
    "K": UnitDef("temperature", 1.0, 0.0, "K"),
    "degC": UnitDef("temperature", 1.0, 273.15, "K"),
    "C": UnitDef("temperature", 1.0, 273.15, "K"),
    "J/mol": UnitDef("energy_per_mol", 1.0, 0.0, "J/mol"),
    "kJ/mol": UnitDef("energy_per_mol", 1000.0, 0.0, "J/mol"),
    "mol/m^3": UnitDef("concentration", 1.0, 0.0, "mol/m^3"),
    "mol/L": UnitDef("concentration", 1000.0, 0.0, "mol/m^3"),
    "mol/m3": UnitDef("concentration", 1.0, 0.0, "mol/m^3"),
    "m^3/s": UnitDef("vol_flow", 1.0, 0.0, "m^3/s"),
    "L/s": UnitDef("vol_flow", 1e-3, 0.0, "m^3/s"),
    "L/min": UnitDef("vol_flow", 1e-3 / 60.0, 0.0, "m^3/s"),
    "m^3/h": UnitDef("vol_flow", 1.0 / 3600.0, 0.0, "m^3/s"),
    "m^3": UnitDef("volume", 1.0, 0.0, "m^3"),
    "L": UnitDef("volume", 1e-3, 0.0, "m^3"),
    "s": UnitDef("time", 1.0, 0.0, "s"),
    "min": UnitDef("time", 60.0, 0.0, "s"),
    "h": UnitDef("time", 3600.0, 0.0, "s"),
    "-": UnitDef("dimensionless", 1.0, 0.0, "-"),
    "1/s": UnitDef("rate_const_1", 1.0, 0.0, "1/s"),
    "J/mol/K": UnitDef("entropy_molar", 1.0, 0.0, "J/mol/K"),
    "kJ/mol/K": UnitDef("entropy_molar", 1000.0, 0.0, "J/mol/K"),
    "W/K": UnitDef("heat_cap_rate", 1.0, 0.0, "W/K"),
    "kW/K": UnitDef("heat_cap_rate", 1000.0, 0.0, "W/K"),
    "W": UnitDef("power", 1.0, 0.0, "W"),
    "kW": UnitDef("power", 1000.0, 0.0, "W"),
}


def is_known_unit(unit: str) -> bool:
    """등록된 단위인지 여부를 돌려준다."""
    return unit in _UNITS


def dimension_of(unit: str) -> str:
    """단위의 물리 차원 이름을 돌려준다. 미등록이면 UnitError."""
    if unit not in _UNITS:
        raise UnitError(f"미등록 단위: '{unit}'. core/units.py 의 _UNITS 에 추가하세요.")
    return _UNITS[unit].dimension


def si_unit_of(unit: str) -> str:
    """해당 차원의 SI 기준 단위를 돌려준다."""
    return _UNITS[unit].si_unit if unit in _UNITS else unit


def to_si(value: float, unit: str) -> float:
    """사용자 단위 값을 SI 값으로 변환한다."""
    if unit not in _UNITS:
        raise UnitError(f"미등록 단위: '{unit}'")
    u = _UNITS[unit]
    return value * u.factor + u.offset


def from_si(value_si: float, unit: str) -> float:
    """SI 값을 지정한 사용자 단위로 되돌린다(출력 경계용)."""
    if unit not in _UNITS:
        raise UnitError(f"미등록 단위: '{unit}'")
    u = _UNITS[unit]
    return (value_si - u.offset) / u.factor
