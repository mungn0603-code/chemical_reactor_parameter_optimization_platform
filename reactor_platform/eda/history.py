"""eda/history.py — Undo / Redo / 변경 이력 관리.

모든 전처리는 되돌릴 수 있어야 한다. HistoryManager 는 데이터프레임의 스냅샷을
스택으로 관리하고, 각 변경에 대해 (적용 시간 · 변경 내용 · 적용 사용자) 를 기록한다.

동작 모델
---------
- apply(df, description, user) : 현재 상태 위에 새 스냅샷을 쌓는다(=redo 스택 비움).
- undo() / redo()             : 포인터를 이동해 이전/다음 스냅샷을 현재로 만든다.
- current()                   : 현재 데이터프레임.
- records()                   : 사람이 읽는 이력 목록.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class HistoryRecord:
    """한 번의 변경 이력."""

    step: int
    description: str
    user: str
    timestamp: str
    n_rows: int
    n_cols: int


class HistoryManager:
    """데이터프레임 스냅샷 기반 Undo/Redo 관리자."""

    def __init__(self, df: pd.DataFrame, user: str = "user") -> None:
        # 스택: 각 원소는 (DataFrame, HistoryRecord).
        self._stack: list[tuple[pd.DataFrame, HistoryRecord]] = []
        self._pointer: int = -1
        self._push(df.copy(), "초기 데이터 로드", user)

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _push(self, df: pd.DataFrame, description: str, user: str) -> None:
        rec = HistoryRecord(
            step=len(self._stack),
            description=description,
            user=user,
            timestamp=self._now(),
            n_rows=int(df.shape[0]),
            n_cols=int(df.shape[1]),
        )
        self._stack.append((df, rec))
        self._pointer = len(self._stack) - 1

    def apply(self, df: pd.DataFrame, description: str, user: str = "user") -> pd.DataFrame:
        """새 스냅샷을 현재 위에 쌓는다. 이후 redo 이력은 폐기된다."""
        # 현재 포인터 뒤(redo 대상)를 잘라낸다.
        self._stack = self._stack[: self._pointer + 1]
        self._push(df.copy(), description, user)
        return self.current()

    def can_undo(self) -> bool:
        return self._pointer > 0

    def can_redo(self) -> bool:
        return self._pointer < len(self._stack) - 1

    def undo(self) -> pd.DataFrame:
        """한 단계 되돌린다."""
        if not self.can_undo():
            return self.current()
        self._pointer -= 1
        return self.current()

    def redo(self) -> pd.DataFrame:
        """한 단계 다시 적용한다."""
        if not self.can_redo():
            return self.current()
        self._pointer += 1
        return self.current()

    def current(self) -> pd.DataFrame:
        """현재 데이터프레임(복사본)."""
        return self._stack[self._pointer][0].copy()

    def current_record(self) -> HistoryRecord:
        """현재 상태의 이력 레코드."""
        return self._stack[self._pointer][1]

    def records(self) -> list[HistoryRecord]:
        """전체 이력 레코드 목록(과거 → 현재 → redo 대상 순)."""
        return [rec for _, rec in self._stack]

    def history_table(self) -> pd.DataFrame:
        """이력을 표(DataFrame)로 만든다(UI 표시용)."""
        rows = []
        for i, (_, rec) in enumerate(self._stack):
            marker = "▶ 현재" if i == self._pointer else ("· redo" if i > self._pointer else "")
            rows.append({
                "step": rec.step,
                "적용 시간": rec.timestamp,
                "변경 내용": rec.description,
                "사용자": rec.user,
                "행": rec.n_rows,
                "열": rec.n_cols,
                "상태": marker,
            })
        return pd.DataFrame(rows)
