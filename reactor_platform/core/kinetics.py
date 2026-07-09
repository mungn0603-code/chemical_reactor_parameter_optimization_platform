"""core/kinetics.py — 반응속도론(Arrhenius, 속도식).

입력은 모두 SI 값이라고 가정한다.
Arrhenius : k(T) = A * exp(-Ea / (R * T))
속도식(n차): -r_A = k * C_A^n
"""
from __future__ import annotations

import math

R_GAS: float = 8.314462618  # J/(mol*K)


def arrhenius_k(A: float, Ea_si: float, T_si: float, R: float = R_GAS) -> float:
    """Arrhenius 식으로 속도상수 k 를 계산한다."""
    if T_si <= 0:
        raise ValueError("절대온도 T 는 0K보다 커야 합니다.")
    return A * math.exp(-Ea_si / (R * T_si))


def rate_of_reaction(k: float, C_A_si: float, order: float) -> float:
    """n차 단일반응의 반응속도 -r_A 를 계산한다."""
    if C_A_si < 0:
        raise ValueError("농도는 음수가 될 수 없습니다.")
    return k * (C_A_si ** order)
