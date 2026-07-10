"""test_eda_outlier.py — 이상치 탐지 검증."""
import numpy as np
import pandas as pd

from reactor_platform.eda.outlier import detect_outliers


def _df_with_outlier():
    base = list(np.random.default_rng(0).normal(10, 1, 50))
    base[0] = 999.0  # 명백한 이상치
    return pd.DataFrame({"v": base})


def test_iqr_detects_extreme_value():
    res = detect_outliers(_df_with_outlier(), method="iqr")
    assert res.n_outliers >= 1
    assert 0 in res.indices()


def test_zscore_detects_extreme_value():
    res = detect_outliers(_df_with_outlier(), method="zscore")
    assert res.n_outliers >= 1


def test_isolation_forest_falls_back_or_works():
    # sklearn 유무와 무관하게 결과가 나와야 한다.
    res = detect_outliers(_df_with_outlier(), method="isolation_forest")
    assert res.n_outliers >= 1
    assert res.method in ("isolation_forest", "iqr")


def test_no_numeric_columns_returns_empty():
    df = pd.DataFrame({"c": ["a", "b", "c"]})
    res = detect_outliers(df)
    assert res.n_outliers == 0 and res.columns == []


def test_mask_aligned_to_index():
    df = _df_with_outlier()
    res = detect_outliers(df, method="iqr")
    assert len(res.mask) == len(df)
