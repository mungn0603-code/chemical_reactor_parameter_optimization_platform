"""parameters/validators.py — 계산 전 6단계 검증 파이프라인.

1. 타입 검증   : 값이 숫자인가 / INPUT 인데 비어있지 않은가
2. 단위 검증   : 단위가 등록되어 있는가(미등록 단위 거부)
3. 범위 검증   : min <= value <= max 인가(물리적 한계)
4. SI 환산     : 경계에서 SI로 변환해 파라미터에 저장
5. 물리 일관성 : 파라미터 간 상호 제약(예: 온도>0K, 농도>0)
6. (사후) 자기검증 : 계산 후 결과 타당성 검사는 reactors 쪽 check_result() 가 담당
"""
from __future__ import annotations

from numbers import Real

from ..core import units
from .registry import ParameterRegistry
from .schema import Parameter, Role


class ValidationError(ValueError):
    """검증 실패. message 에 어떤 파라미터가 왜 틀렸는지 담는다."""


def _validate_one(p: Parameter) -> None:
    """파라미터 하나에 대해 1~5단계를 수행한다."""
    if p.role == Role.DERIVED:
        return

    if p.value is None:
        raise ValidationError(f"[{p.label}({p.symbol})] 값이 비어 있습니다.")
    if not isinstance(p.value, Real) or isinstance(p.value, bool):
        raise ValidationError(
            f"[{p.label}({p.symbol})] 숫자가 아닙니다: {p.value!r}"
        )

    if not units.is_known_unit(p.unit):
        raise ValidationError(
            f"[{p.label}({p.symbol})] 미등록 단위 '{p.unit}'. "
            "core/units.py 에 추가하거나 올바른 단위를 쓰세요."
        )

    v = float(p.value)
    if p.min is not None and v < p.min:
        raise ValidationError(
            f"[{p.label}({p.symbol})] 값 {v}{p.unit} 이 최소 {p.min}{p.unit} 보다 작습니다."
        )
    if p.max is not None and v > p.max:
        raise ValidationError(
            f"[{p.label}({p.symbol})] 값 {v}{p.unit} 이 최대 {p.max}{p.unit} 보다 큽니다."
        )

    p._si_value = units.to_si(v, p.unit)


def _validate_physics(reg: ParameterRegistry) -> None:
    """5단계: 파라미터 간 물리 일관성 검사(등록된 것만 검사)."""
    checks = {
        "temperature": ("절대온도", lambda si: si > 0, "0K보다 커야 합니다"),
        "C_A0": ("초기 농도", lambda si: si > 0, "0보다 커야 합니다"),
        "v0": ("부피 유량", lambda si: si > 0, "0보다 커야 합니다"),
        "volume": ("반응기 부피", lambda si: si > 0, "0보다 커야 합니다"),
        "tau": ("체류시간", lambda si: si > 0, "0보다 커야 합니다"),
    }
    for key, (name, ok, msg) in checks.items():
        if reg.has(key):
            p = reg.get(key)
            if p.role != Role.DERIVED and p._si_value is not None and not ok(p._si_value):
                raise ValidationError(f"[{name}] {msg}. (현재 SI값 {p._si_value})")


def validate_registry(reg: ParameterRegistry) -> None:
    """레지스트리 전체를 검증한다(계산 직전 반드시 호출)."""
    for p in reg.all():
        _validate_one(p)
    _validate_physics(reg)
