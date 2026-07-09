"""core/reactors/cstr.py — 등온 정상상태 CSTR.

물질수지(정상상태): C_A0 * X = k * (C_A0 (1 - X))^n * tau,   tau = V / v0
- 1차(n=1) 해석해:  X = k*tau / (1 + k*tau)
- n차: 이분법으로 근 X in (0,1) 을 구한다.
"""
from __future__ import annotations

import math

from ..explain import SpecCard
from ..kinetics import arrhenius_k, rate_of_reaction
from .base import ReactorBase, ReactorResult


def _solve_conversion_nth_order(
    k: float, tau: float, C_A0: float, n: float,
    tol: float = 1e-12, max_iter: int = 200,
) -> float:
    """n차 등온 CSTR 전환율 X 를 이분법으로 구한다."""
    def f(X: float) -> float:
        C_A = C_A0 * (1.0 - X)
        return k * (C_A ** n) * tau - C_A0 * X

    lo, hi = 0.0, 1.0
    flo = f(lo)
    if abs(flo) < tol:
        return 0.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = f(mid)
        if abs(fmid) < tol or (hi - lo) < tol:
            return mid
        if (flo > 0) == (fmid > 0):
            lo, flo = mid, fmid
        else:
            hi = mid
    return 0.5 * (lo + hi)


class CSTR(ReactorBase):
    """등온 정상상태 CSTR 모델."""

    name = "등온 CSTR"

    def required_inputs(self) -> list[str]:
        return [
            "pre_exponential", "activation_energy", "temperature",
            "reaction_order", "C_A0", "v0", "volume", "R",
        ]

    def describe(self) -> SpecCard:
        return SpecCard(
            title="CSTR 전환율 계산",
            what="등온 정상상태 CSTR에서 반응물 A의 전환율 X와 관련 값을 계산",
            inputs=[
                "A: 빈도인자",
                "Ea: 활성화 에너지",
                "T: 절대온도",
                "n: 반응차수",
                "C_A0: 초기 농도",
                "v0: 부피 유량, V: 반응기 부피 (→ 체류시간 tau=V/v0)",
            ],
            formula="k=A·exp(-Ea/RT); C_A0·X = k·(C_A0(1-X))^n·tau; 1차는 X=kτ/(1+kτ)",
            output="X(전환율, 0~1), k(속도상수), tau(체류시간,s), C_A_out(출구농도), rate(-r_A)",
            role="생산량·수율·선택도·경제성 계산의 출발점",
            caution="k>0, tau>0 이어야 하며 결과 X 는 반드시 0~1. 범위 밖이면 사후검증 실패.",
        )

    def _compute(self) -> ReactorResult:
        reg = self.reg
        A = reg.si("pre_exponential")
        Ea = reg.si("activation_energy")
        T = reg.si("temperature")
        n = reg.si("reaction_order")
        C_A0 = reg.si("C_A0")
        v0 = reg.si("v0")
        V = reg.si("volume")
        R = reg.si("R")

        steps: list[str] = []

        k = arrhenius_k(A, Ea, T, R)
        steps.append(f"Arrhenius: k = A·exp(-Ea/RT) = {A:.6g}·exp(-{Ea:.6g}/({R:.6g}·{T:.6g})) = {k:.6g}")

        tau = V / v0
        steps.append(f"체류시간: tau = V/v0 = {V:.6g}/{v0:.6g} = {tau:.6g} s")

        if abs(n - 1.0) < 1e-12:
            X = (k * tau) / (1.0 + k * tau)
            steps.append(f"전환율(1차 해석해): X = kτ/(1+kτ) = {X:.6g}")
        else:
            X = _solve_conversion_nth_order(k, tau, C_A0, n)
            steps.append(f"전환율(n={n:g} 수치해, 이분법): X = {X:.6g}")

        C_A_out = C_A0 * (1.0 - X)
        rate = rate_of_reaction(k, C_A_out, n)
        steps.append(f"출구농도: C_A = C_A0(1-X) = {C_A_out:.6g} mol/m^3")
        steps.append(f"반응속도: -r_A = k·C_A^n = {rate:.6g} mol/(m^3·s)")

        for key, val in (("k", k), ("tau", tau), ("X", X)):
            if reg.has(key):
                reg.set_derived(key, val)

        return ReactorResult(
            values={"k": k, "tau": tau, "X": X, "C_A_out": C_A_out, "rate": rate},
            steps=steps,
        )

    def check_result(self, result: ReactorResult) -> ReactorResult:
        """사후 자기검증: 물리적으로 말이 되는 결과인지 확인."""
        X = result.values["X"]
        k = result.values["k"]
        tau = result.values["tau"]
        if not (0.0 - 1e-9 <= X <= 1.0 + 1e-9):
            result.ok = False
            result.warnings.append(f"전환율 X={X:.4g} 가 0~1 범위를 벗어났습니다.")
        if k <= 0:
            result.ok = False
            result.warnings.append(f"속도상수 k={k:.4g} 가 0 이하입니다.")
        if tau <= 0:
            result.ok = False
            result.warnings.append(f"체류시간 tau={tau:.4g} 가 0 이하입니다.")
        if math.isnan(X) or math.isinf(X):
            result.ok = False
            result.warnings.append("전환율 계산이 수렴하지 않았습니다(NaN/Inf).")
        return result
