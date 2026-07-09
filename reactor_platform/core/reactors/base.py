"""core/reactors/base.py — 모든 반응기의 공통 인터페이스.

모든 반응기는 required_inputs / describe / solve / check_result / report 를 제공한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ...parameters.registry import ParameterRegistry
from ...parameters.validators import validate_registry
from ..explain import SpecCard, render_params


@dataclass
class ReactorResult:
    """반응기 계산 결과."""

    values: dict[str, float]
    steps: list[str] = field(default_factory=list)
    ok: bool = True
    warnings: list[str] = field(default_factory=list)


class ReactorBase(ABC):
    """반응기 추상 클래스."""

    name: str = "reactor"

    def __init__(self, reg: ParameterRegistry) -> None:
        self.reg = reg

    @abstractmethod
    def required_inputs(self) -> list[str]:
        """이 반응기가 필요로 하는 파라미터 키 목록."""

    @abstractmethod
    def describe(self) -> SpecCard:
        """이 반응기 계산의 설명 카드."""

    @abstractmethod
    def _compute(self) -> ReactorResult:
        """실제 계산(하위 클래스 구현). 이 시점엔 이미 검증 완료 상태."""

    @abstractmethod
    def check_result(self, result: ReactorResult) -> ReactorResult:
        """6단계-사후 자기검증: 결과가 물리적으로 타당한지 확인."""

    def solve(self) -> ReactorResult:
        """검증 → 계산 → 사후검증 순으로 안전하게 실행한다."""
        validate_registry(self.reg)
        result = self._compute()
        result = self.check_result(result)
        return result

    def explain(self) -> str:
        """이 반응기가 무엇을 하는지 + 필요한 입력 설명(자기설명)."""
        params = [self.reg.get(k) for k in self.required_inputs() if self.reg.has(k)]
        return self.describe().render() + "\n\n  [필요 입력]\n" + render_params(params)

    def report(self, result: ReactorResult | None = None) -> str:
        """입력→공식→중간값→결과→검증 통과 여부를 담은 계산 리포트."""
        if result is None:
            result = self.solve()
        lines = [f"===== {self.name} 계산 리포트 =====", "", self.explain(), "", "  [계산 과정]"]
        lines += [f"    {s}" for s in result.steps]
        lines += ["", "  [결과]"]
        for k, v in result.values.items():
            lines.append(f"    {k} = {v:.6g}")
        status = "통과 ✅" if result.ok else "실패 ❌"
        lines += ["", f"  [사후 자기검증] {status}"]
        for w in result.warnings:
            lines.append(f"    ⚠ {w}")
        return "\n".join(lines)
