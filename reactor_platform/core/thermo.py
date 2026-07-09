"""core/thermo.py - Thermodynamic feasibility (M2).

From dH, dS, T compute dG = dH - T*dS and K_eq = exp(-dG/(R*T)) and classify
spontaneity. Thermodynamic feasibility (dG<0) is NOT the same as kinetic
feasibility; both are reported side by side. Inputs come from the registry (SI).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..parameters.registry import ParameterRegistry
from ..parameters.validators import validate_registry
from .explain import SpecCard


def gibbs_free_energy(dH_si: float, dS_si: float, T_si: float) -> float:
    """dG = dH - T * dS. Inputs in SI (J/mol, J/mol/K, K)."""
    if T_si <= 0:
        raise ValueError("Absolute temperature must be > 0 K.")
    return dH_si - T_si * dS_si


def equilibrium_constant(dG_si: float, T_si: float, R: float) -> float:
    """K_eq = exp(-dG / (R * T))."""
    if T_si <= 0:
        raise ValueError("Absolute temperature must be > 0 K.")
    return math.exp(-dG_si / (R * T_si))


def spontaneity_label(dG_si: float, tol: float = 1e-6) -> str:
    """Return a Korean verdict for the sign of dG."""
    if dG_si < -tol:
        return "자발적"
    if dG_si > tol:
        return "비자발적"
    return "평형"


@dataclass
class ThermoResult:
    """Result of a thermodynamic feasibility analysis."""

    values: dict[str, float]
    verdict: str
    steps: list[str] = field(default_factory=list)
    ok: bool = True
    warnings: list[str] = field(default_factory=list)


class ThermoAnalyzer:
    """Parameter-driven, self-documenting thermodynamic feasibility check."""

    name = "열역학 반응 가능성"

    def __init__(self, reg: ParameterRegistry) -> None:
        self.reg = reg

    def required_inputs(self) -> list[str]:
        return ["dH", "dS", "temperature", "R"]

    def describe(self) -> SpecCard:
        return SpecCard(
            title="열역학 반응 가능성 판정",
            what="dH, dS, T 로부터 dG, K_eq 를 구하고 자발성/반응 가능 여부를 판정",
            inputs=[
                "dH: 반응 엔탈피 변화",
                "dS: 반응 엔트로피 변화",
                "T: 절대온도",
                "R: 기체 상수(상수)",
            ],
            formula="dG = dH - T·dS;  K_eq = exp(-dG/RT)",
            output="dG(J/mol), K_eq(-), 판정(자발적/평형/비자발적)",
            role="반응 가능 여부(열역학) 판정 - 속도론적 가능성과는 별개",
            caution="dG<0 이라도 반응속도(k)가 작으면 실제로는 느릴 수 있음(속도론 별도 판정).",
        )

    def solve(self) -> ThermoResult:
        """Validate the registry, then compute dG, K_eq and the verdict."""
        validate_registry(self.reg)
        dH = self.reg.si("dH")
        dS = self.reg.si("dS")
        T = self.reg.si("temperature")
        R = self.reg.si("R")

        steps: list[str] = []
        dG = gibbs_free_energy(dH, dS, T)
        steps.append(f"dG = dH - T·dS = {dH:.6g} - {T:.6g}·{dS:.6g} = {dG:.6g} J/mol")
        Keq = equilibrium_constant(dG, T, R)
        steps.append(f"K_eq = exp(-dG/RT) = exp({-dG:.6g}/({R:.6g}·{T:.6g})) = {Keq:.6g}")
        verdict = spontaneity_label(dG)
        sign = "<" if dG < 0 else ">" if dG > 0 else "="
        steps.append(f"판정: dG {sign} 0 -> {verdict}")

        for key, val in (("dG", dG), ("K_eq", Keq)):
            if self.reg.has(key):
                self.reg.set_derived(key, val)

        result = ThermoResult(values={"dG": dG, "K_eq": Keq}, verdict=verdict, steps=steps)
        return self._check(result)

    def _check(self, result: ThermoResult) -> ThermoResult:
        """Post-hoc self-check: K_eq must be finite and positive."""
        Keq = result.values["K_eq"]
        if Keq <= 0 or math.isnan(Keq) or math.isinf(Keq):
            result.ok = False
            result.warnings.append(f"K_eq={Keq:.4g} 가 물리적으로 타당하지 않습니다.")
        return result

    def explain(self) -> str:
        """Self-documenting description + required inputs."""
        from .explain import render_params

        params = [self.reg.get(k) for k in self.required_inputs() if self.reg.has(k)]
        return self.describe().render() + "\n\n  [필요 입력]\n" + render_params(params)

    def report(self, result: ThermoResult | None = None) -> str:
        """input -> formula -> intermediate -> verdict -> self-check report."""
        if result is None:
            result = self.solve()
        lines = [f"===== {self.name} 리포트 =====", "", self.explain(), "", "  [계산 과정]"]
        lines += [f"    {s}" for s in result.steps]
        lines += ["", "  [결과]"]
        for k, v in result.values.items():
            lines.append(f"    {k} = {v:.6g}")
        lines.append(f"    판정 = {result.verdict}")
        status = "통과" if result.ok else "실패"
        lines += ["", f"  [사후 자기검증] {status}"]
        for w in result.warnings:
            lines.append(f"    ! {w}")
        return "\n".join(lines)
