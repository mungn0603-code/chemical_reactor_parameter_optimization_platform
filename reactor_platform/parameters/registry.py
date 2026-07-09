"""parameters/registry.py — ParameterRegistry (단일 진실 원천).

역할
----
프로그램에서 쓰는 모든 물리량을 한 곳에 모아 둔다. 계산 함수는 값을 스스로
'발명'하지 않고 반드시 이 레지스트리에서 받아서 쓴다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .schema import Parameter, Role


class RegistryError(KeyError):
    """레지스트리 조회/등록 오류."""


class ParameterRegistry:
    """파라미터들의 단일 저장소."""

    def __init__(self) -> None:
        self._params: dict[str, Parameter] = {}

    def add(self, param: Parameter) -> None:
        """새 파라미터를 등록한다. 키 중복 시 오류."""
        if param.key in self._params:
            raise RegistryError(f"이미 등록된 파라미터 키: '{param.key}'")
        self._params[param.key] = param

    def get(self, key: str) -> Parameter:
        """키로 파라미터를 조회한다. 없으면 오류."""
        if key not in self._params:
            raise RegistryError(f"등록되지 않은 파라미터: '{key}'")
        return self._params[key]

    def has(self, key: str) -> bool:
        return key in self._params

    def all(self) -> list[Parameter]:
        """등록된 모든 파라미터 목록."""
        return list(self._params.values())

    def by_role(self, role: Role) -> list[Parameter]:
        """역할별 파라미터 목록(예: INPUT 만 UI에 노출할 때)."""
        return [p for p in self._params.values() if p.role == role]

    def set_value(self, key: str, value: float) -> None:
        """사용자 입력 값을 설정한다. DERIVED 는 직접 입력 금지."""
        p = self.get(key)
        if p.role == Role.DERIVED:
            raise RegistryError(
                f"'{key}' 는 계산 결과(derived) 파라미터이므로 직접 입력할 수 없습니다."
            )
        p.value = value
        p._si_value = None

    def set_derived(self, key: str, si_value: float, display_value: Optional[float] = None) -> None:
        """계산 결과를 DERIVED 파라미터에 기록한다(시스템 전용)."""
        p = self.get(key)
        if p.role != Role.DERIVED:
            raise RegistryError(f"'{key}' 는 derived 파라미터가 아닙니다.")
        p._si_value = si_value
        p.value = display_value if display_value is not None else si_value

    def si(self, key: str) -> float:
        """검증된 SI 값을 바로 꺼낸다(계산 함수에서 사용)."""
        return self.get(key).si_value

    def from_yaml(self, path: str | Path) -> None:
        """YAML 카탈로그에서 파라미터 정의를 읽어 등록한다."""
        import yaml

        def _num(x: object) -> Optional[float]:
            """숫자로 해석 가능한 값을 float로 변환한다. None/그 외는 None."""
            if x is None or isinstance(x, bool):
                return None
            if isinstance(x, (int, float)):
                return float(x)
            if isinstance(x, str):
                try:
                    return float(x)
                except ValueError:
                    return None
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        for item in data:
            self.add(
                Parameter(
                    key=item["key"],
                    label=item["label"],
                    symbol=item["symbol"],
                    unit=item["unit"],
                    role=Role(item["role"]),
                    description=item["description"],
                    value=_num(item.get("value")),
                    min=_num(item.get("min")),
                    max=_num(item.get("max")),
                    source=item.get("source", ""),
                )
            )
