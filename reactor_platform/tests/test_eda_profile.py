"""test_eda_profile.py — 데이터 프로파일링 진단 검증."""
import numpy as np
import pandas as pd
import pytest

from reactor_platform.eda.profile import profile_dataframe
from reactor_platform.eda.sample import make_sample_dataset


def test_profile_counts_rows_and_cols():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    p = profile_dataframe(df)
    assert p.n_rows == 3 and p.n_cols == 2
    assert p.numeric_cols == ["a"] and p.categorical_cols == ["b"]


def test_profile_detects_missing_and_duplicates():
    df = pd.DataFrame({"a": [1.0, None, 3.0, 3.0], "b": [1, 1, 1, 1]})
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    p = profile_dataframe(df)
    assert p.total_missing == 1
    assert p.n_duplicates >= 1


def test_profile_finds_strong_correlation():
    x = np.arange(50, dtype=float)
    df = pd.DataFrame({"x": x, "y": 2 * x + 1})
    p = profile_dataframe(df)
    assert p.strong_pairs
    a, b, r = p.strong_pairs[0]
    assert abs(r) > 0.99


def test_quality_score_bounds():
    p = profile_dataframe(make_sample_dataset())
    assert 0.0 <= p.quality_score <= 100.0


def test_profile_does_not_mutate_input():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    before = df.copy()
    profile_dataframe(df)
    pd.testing.assert_frame_equal(df, before)


def test_summary_text_is_korean():
    p = profile_dataframe(make_sample_dataset())
    assert "데이터 품질 점수" in p.summary_text()


def test_type_error_on_non_dataframe():
    with pytest.raises(TypeError):
        profile_dataframe([1, 2, 3])
