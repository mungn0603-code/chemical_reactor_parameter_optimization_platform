"""core/explain.py — 자기설명(Self-Documenting) 엔진.

- explain_parameter(p)      : 파라미터 하나의 뜻·단위·역할·범위
- SpecCard                  : 수식(계산 함수)의 설명 카드
- render_params             : 사람이 읽는 텍스트로 렌더링
"""
from __future__ import annotations

from dataclasses import dataclass

from ..parameters.schema import Parameter, Role

_ROLE_KR = {
    Role.INPUT: "입력값",
    Role.CONSTANT: "상수(잠금)",
    Role.DERIVED: "계산결과",
}


def explain_parameter(p: Parameter) -> str:
    """파라미터 하나를 한 줄 설명으로 만든다."""
    unit = "" if p.unit == "-" else f" {p.unit}"
    rng = ""
    if p.min is not None or p.max is not None:
        lo = "-∞" if p.min is None else p.min
        hi = "∞" if p.max is None else p.max
        rng = f" | 유효범위 {lo}~{hi}{unit}"
    val = "(미입력)" if p.value is None else f"{p.value}{unit}"
    return (
        f"- {p.label}({p.symbol}) [{_ROLE_KR[p.role]}] = {val}{rng}\n"
        f"    ↳ {p.description}"
    )


def render_params(params: list[Parameter]) -> str:
    """파라미터 목록을 설명 블록으로 렌더링."""
    return "\n".join(explain_parameter(p) for p in params)


@dataclass
class SpecCard:
    """하나의 계산(수식)에 대한 설명 카드."""

    title: str
    what: str
    inputs: list[str]
    formula: str
    output: str
    role: str
    caution: str

    def render(self) -> str:
        """설명 카드를 텍스트로 출력."""
        inp = "\n".join(f"      · {s}" for s in self.inputs)
        return (
            f"[설명 카드: {self.title}]\n"
            f"  - 무엇을: {self.what}\n"
            f"  - 입력:\n{inp}\n"
            f"  - 공식: {self.formula}\n"
            f"  - 출력: {self.output}\n"
            f"  - 역할: {self.role}\n"
            f"  - 주의: {self.caution}"
        )
