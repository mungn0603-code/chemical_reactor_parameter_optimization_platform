"""demo.py — 입력 → 검증 → 계산 → 설명 리포트 데모.

실행:
    python -m reactor_platform.demo
"""
from __future__ import annotations

from pathlib import Path

from .parameters.registry import ParameterRegistry
from .core.reactors.cstr import CSTR

CATALOG = Path(__file__).parent / "parameters" / "catalog" / "cstr_example.yaml"


def main() -> None:
    reg = ParameterRegistry()
    reg.from_yaml(CATALOG)
    reactor = CSTR(reg)
    result = reactor.solve()
    print(reactor.report(result))


if __name__ == "__main__":
    main()
