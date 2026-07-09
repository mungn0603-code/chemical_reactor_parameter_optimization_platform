"""parameters/schema.py — Parameter 객체 정의.

역할
----
숫자 하나(값)가 아니라, 그 값이 '무엇이고 / 어떤 단위이며 / 어떤 역할이고 /
어떤 범위가 유효한지'를 함께 담는 하나의 묶음(Parameter)을 정의한다.
이것이 파라미터 주도 설계의 최소 단위이며, 자기설명과 검증의 기반이다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Role(str, Enum):
    """파라미터의 역할.

    - INPUT    : 사용자가 직접 입력하는 값 (운전조건·물성). 예: T, C_A0, A, Ea, n
    - CONSTANT : 바뀌면 안 되는 상수. UI에서 잠금. 예: 기체상수 R
    - DERIVED  : 계산으로만 채워지는 결과. 사용자 입력 금지. 예: k, X, tau
    """

    INPUT = "input"
    CONSTANT = "constant"
    DERIVED = "derived"


@dataclass
class Parameter:
    """검증 가능한 하나의 물리량.

    필드
    ----
    key : str
        내부 고유 키(영문). 계산 코드가 이 키로 값을 찾는다.
    label : str
        사용자용 한글 이름.
    symbol : str
        수식 기호(예: Ea, C_A0).
    unit : str
        사용자가 입력하는 단위(core/units.py 에 등록된 것).
    role : Role
        input / constant / derived.
    description : str
        이 값이 무엇이고 왜 필요한지에 대한 한글 설명(자기설명의 핵심).
    value : float | None
        현재 값(사용자 단위 기준). derived 는 계산 후 채워진다.
    min, max : float | None
        물리적으로 허용되는 범위(사용자 단위 기준). 검증에 사용.
    source : str
        값의 출처/신뢰도 메모(문헌·가정 등).
    """

    key: str
    label: str
    symbol: str
    unit: str
    role: Role
    description: str
    value: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    source: str = ""
    # 내부 계산용 SI 값(검증 파이프라인이 채운다). 직접 설정하지 말 것.
    _si_value: Optional[float] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # 설명 누락은 설계 위반 → 생성 시점에 바로 막는다(자기설명 강제).
        if not self.description or not self.description.strip():
            raise ValueError(
                f"파라미터 '{self.key}' 에 description(한글 설명)이 없습니다. "
                "모든 파라미터는 설명을 가져야 합니다."
            )
        if not isinstance(self.role, Role):
            self.role = Role(self.role)

    @property
    def si_value(self) -> float:
        """검증을 통과해 SI로 변환된 값. 검증 전 접근하면 오류."""
        if self._si_value is None:
            raise RuntimeError(
                f"파라미터 '{self.key}' 는 아직 검증되지 않았습니다. "
                "먼저 validators.validate_registry() 를 통과시키세요."
            )
        return self._si_value
