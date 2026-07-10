"""test_eda_history.py — Undo/Redo/이력 관리 검증."""
import pandas as pd

from reactor_platform.eda.history import HistoryManager
from reactor_platform.eda.preprocessing import apply_action


def _base():
    return pd.DataFrame({"a": [1.0, None, 3.0, 3.0]})


def test_initial_snapshot_recorded():
    h = HistoryManager(_base(), user="tester")
    assert len(h.records()) == 1
    assert h.records()[0].user == "tester"
    assert not h.can_undo() and not h.can_redo()


def test_apply_then_undo_redo():
    h = HistoryManager(_base())
    out = apply_action(h.current(), "impute_median", "a")
    h.apply(out, "median impute")
    assert h.current()["a"].isna().sum() == 0
    assert h.can_undo()

    h.undo()
    assert h.current()["a"].isna().sum() == 1  # 되돌려짐
    assert h.can_redo()

    h.redo()
    assert h.current()["a"].isna().sum() == 0  # 다시 적용됨


def test_new_apply_clears_redo():
    h = HistoryManager(_base())
    h.apply(apply_action(h.current(), "impute_mean", "a"), "mean")
    h.undo()
    assert h.can_redo()
    h.apply(apply_action(h.current(), "drop_missing_rows", "a"), "dropna")
    assert not h.can_redo()  # 새 분기 → redo 폐기


def test_history_table_marks_current():
    h = HistoryManager(_base())
    h.apply(apply_action(h.current(), "drop_duplicates"), "dedup")
    table = h.history_table()
    assert (table["상태"] == "▶ 현재").sum() == 1


def test_records_track_shape():
    h = HistoryManager(_base())
    h.apply(apply_action(h.current(), "drop_duplicates"), "dedup")
    assert h.current_record().n_rows == 3  # 4행 → 중복 1개 제거
