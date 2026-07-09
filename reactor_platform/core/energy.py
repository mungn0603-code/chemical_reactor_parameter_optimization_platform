"""core/energy.py - Steady-state energy balance / heat duty (M3).

Q = Cp_flow * (T - T_feed) + dH_rxn * (F_A0 * X), F_A0*X = v0*C_A0*X.
Q>0 heating required, Q<0 cooling (report |Q|). X is obtained by reusing the
validated CSTR engine, so nothing is hard-coded.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parameters.registry import ParameterRegistry
from .explain import SpecCard
from .reactors.cstr import CSTR


def reaction_heat_rate(dH_rxn_si: float, mol_rate_si: float) -> float:
    """Heat released/absorbed by reaction = dH_rxn * (mol converted per s) [W]."""
    return dH_rxn_si * mol_rate_si


def sensible_heat_rate(cp_flow_si: float, T_si: float, T_feed_si: float) -> float:
    """Sensible heat to bring the feed to reactor temperature [W]."""
    return cp_flow_si * (T_si - T_feed_si)


def duty_label(Q_si: float, tol: float = 1e-9) -> str:
    """Korean label for the sign of the duty."""
    if Q_si > tol:
        return "가열"
    if Q_si < -tol:
        return "냉각"
    return "단열"


@dataclass
class EnergyResult:
    """Result of the energy-balance calculation."""

    values: dict[str, float]
    duty: str
    steps: list[str] = field(default_factory=list)
    ok: bool = True
    warnings: list[str] = field(default_factory=list)


class EnergyBalance:
    """Parameter-driven, self-documenting CSTR heat-duty calculator."""

    name = "CSTR 에너지수지"

    def __init__(self, reg: ParameterRegistry) -> None:
        self.reg = reg

    def required_inputs(self) -> list[str]:
        return ["dH_rxn", "cp_flow", "T_feed", "temperature", "C_A0", "v0"]

    def describe(self) -> SpecCard:
        return SpecCard(
            title="CSTR 열부하(heat duty) 계산",
            what="정상상태 CSTR 운전에 필요한 외부 열부하 Q 와 가열/냉각 여부를 계산",
            inputs=[
                "dH_rxn: 반응열(몰당)",
                "cp_flow: 공급 열용량 유량",
                "T_feed: 공급 온도, T: 반응 온도",
                "X: CSTR 전환율(엔진에서 계산)",
            ],
            formula="Q = cp_flow·(T-T_feed) + dH_rxn·(v0·C_A0·X)",
            output="Q(W), 현열항, 반응열항, 판정(가열/냉각/단열)",
            role="공정 안정성·유틸리티(냉각수/스팀) 산정의 기초",
            caution="발열 반응(dH_rxn<0)은 보통 냉각이 필요. X 는 CSTR 엔진 결과를 재사용.",
        )

    def solve(self) -> EnergyResult:
        """Solve the CSTR for X, then compute the heat duty."""
        x_result = CSTR(self.reg).solve()
        X = x_result.values["X"]

        dH = self.reg.si("dH_rxn")
        cp = self.reg.si("cp_flow")
        T = self.reg.si("temperature")
        T_feed = self.reg.si("T_feed")
        c_a0 = self.reg.si("C_A0")
        v0 = self.reg.si("v0")

        mol_rate = v0 * c_a0 * X
        q_rxn = reaction_heat_rate(dH, mol_rate)
        q_sens = sensible_heat_rate(cp, T, T_feed)
        Q = q_rxn + q_sens

        steps = [
            f"전환율(CSTR): X = {X:.6g}",
            f"전환 몰속도: v0·C_A0·X = {v0:.6g}·{c_a0:.6g}·{X:.6g} = {mol_rate:.6g} mol/s",
            f"반응열항: dH_rxn·mol_rate = {dH:.6g}·{mol_rate:.6g} = {q_rxn:.6g} W",
            f"현열항: cp_flow·(T-T_feed) = {cp:.6g}·({T:.6g}-{T_feed:.6g}) = {q_sens:.6g} W",
            f"열부하: Q = {q_rxn:.6g} + {q_sens:.6g} = {Q:.6g} W -> {duty_label(Q)}",
        ]

        for key, val in (("Q", Q), ("X", X)):
            if self.reg.has(key) and self.reg.get(key).role.value == "derived":
                self.reg.set_derived(key, val)

        result = EnergyResult(
            values={"Q": Q, "Q_reaction": q_rxn, "Q_sensible": q_sens, "X": X},
            duty=duty_label(Q),
            steps=steps,
        )
        return self._check(result)

    def _check(self, result: EnergyResult) -> EnergyResult:
        """Post-hoc self-check: components must sum to Q."""
        Q = result.values["Q"]
        parts = result.values["Q_reaction"] + result.values["Q_sensible"]
        if abs(parts - Q) > 1e-6 * max(1.0, abs(Q)):
            result.ok = False
            result.warnings.append("현열항 + 반응열항 이 Q 와 일치하지 않습니다.")
        return result

    def explain(self) -> str:
        """Self-documenting description + required inputs."""
        from .explain import render_params

        params = [self.reg.get(k) for k in self.required_inputs() if self.reg.has(k)]
        return self.describe().render() + "\n\n  [필요 입력]\n" + render_params(params)

    def report(self, result: EnergyResult | None = None) -> str:
        """input -> formula -> intermediate -> duty -> self-check report."""
        if result is None:
            result = self.solve()
        lines = [f"===== {self.name} 리포트 =====", "", self.explain(), "", "  [계산 과정]"]
        lines += [f"    {s}" for s in result.steps]
        lines += ["", "  [결과]"]
        for k, v in result.values.items():
            lines.append(f"    {k} = {v:.6g}")
        lines.append(f"    판정 = {result.duty}")
        status = "통과" if result.ok else "실패"
        lines += ["", f"  [사후 자기검증] {status}"]
        for w in result.warnings:
            lines.append(f"    ! {w}")
        return "\n".join(lines)
