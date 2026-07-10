"""test_eda_preprocessing.py — 전처리 제안·적용 검증(원본 불변 포함)."""
import pandas as pd
import pytest

from reactor_platform.eda.preprocessing import apply_action, suggest_preprocessing


def test_suggest_detects_missing_and_duplicate():
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": [1, 1, 1]})
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    issues = {s.issue for s in suggest_preprocessing(df)}
    assert "missing" in issues


def test_apply_does_not_mutate_input():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    before = df.copy()
    apply_action(df, "impute_median", "a")
    pd.testing.assert_frame_equal(df, before)


def test_impute_median_fills_missing():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    out = apply_action(df, "impute_median", "a")
    assert out["a"].isna().sum() == 0
    assert out["a"].iloc[1] == 2.0


def test_drop_duplicates_reduces_rows():
    df = pd.DataFrame({"a": [1, 1, 2]})
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    out = apply_action(df, "drop_duplicates")
    assert len(out) < len(df)


def test_winsorize_caps_extreme():
    df = pd.DataFrame({"a": [1.0, 2, 3, 4, 5, 6, 7, 8, 9, 1000]})
    out = apply_action(df, "winsorize", "a")
    assert out["a"].max() < 1000


def test_remove_outliers_drops_rows():
    df = pd.DataFrame({"a": [1.0, 2, 3, 4, 5, 6, 7, 8, 9, 1000]})
    out = apply_action(df, "remove_outliers", "a")
    assert 1000 not in out["a"].values


def test_standardize_zero_mean():
    df = pd.DataFrame({"a": [1.0, 2, 3, 4, 5]})
    out = apply_action(df, "standardize", "a")
    assert abs(out["a"].mean()) < 1e-9


def test_onehot_expands_columns():
    df = pd.DataFrame({"c": ["a", "b", "a"]})
    out = apply_action(df, "encode_onehot", "c")
    assert "c" not in out.columns
    assert out.shape[1] >= 2


def test_unknown_action_raises():
    df = pd.DataFrame({"a": [1.0]})
    with pytest.raises(ValueError):
        apply_action(df, "nope", "a")
