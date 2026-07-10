"""eda/outlier.py — 이상치 탐지.

여러 방법으로 이상치를 탐지하고 공통 결과(OutlierResult)로 돌려준다.

지원 방법
---------
- "iqr"     : Tukey fence(Q1-1.5·IQR ~ Q3+1.5·IQR) 밖을 이상치로 본다(기본).
- "zscore"  : |z| > 임계값(기본 3.0)을 이상치로 본다.
- "isolation_forest" : scikit-learn IsolationForest(다변량). 미설치 시 IQR 로 대체.
- "lof"     : scikit-learn LocalOutlierFactor(다변량). 미설치 시 IQR 로 대체.

sklearn 미설치 환경에서도 iqr / zscore 는 항상 동작한다.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

_IQR_K = 1.5
_Z_THRESH = 3.0


@dataclass
class OutlierResult:
    """이상치 탐지 결과."""

    method: str
    columns: list[str]
    # df 인덱스에 정렬된 bool 마스크. True = 이상치.
    mask: pd.Series
    n_outliers: int

    def indices(self) -> list:
        """이상치 행의 인덱스 목록."""
        return list(self.mask[self.mask].index)


def _iqr_mask(df: pd.DataFrame, columns: list[str], k: float) -> pd.Series:
    """열별 IQR 이상치를 OR 결합한 행 마스크."""
    mask = pd.Series(False, index=df.index)
    for col in columns:
        s = pd.to_numeric(df[col], errors="coerce")
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lo = q1 - k * iqr
        hi = q3 + k * iqr
        mask = mask | (s < lo) | (s > hi)
    return mask.fillna(False)


def _zscore_mask(df: pd.DataFrame, columns: list[str], thresh: float) -> pd.Series:
    """열별 z-score 이상치를 OR 결합한 행 마스크."""
    mask = pd.Series(False, index=df.index)
    for col in columns:
        s = pd.to_numeric(df[col], errors="coerce")
        std = s.std()
        if pd.isna(std) or std == 0:
            continue
        z = (s - s.mean()) / std
        mask = mask | (z.abs() > thresh)
    return mask.fillna(False)


def _model_mask(df: pd.DataFrame, columns: list[str], method: str) -> pd.Series:
    """IsolationForest / LOF 다변량 이상치 마스크. sklearn 필요."""
    data = df[columns].apply(pd.to_numeric, errors="coerce")
    # 결측은 열 평균으로 임시 대치(모델 입력용, 원본은 변경하지 않음).
    data = data.fillna(data.mean(numeric_only=True))
    valid = data.dropna(how="any")
    mask = pd.Series(False, index=df.index)
    if len(valid) < 5:
        return mask

    if method == "isolation_forest":
        from sklearn.ensemble import IsolationForest

        model = IsolationForest(random_state=0, contamination="auto")
        pred = model.fit_predict(valid.values)
    else:  # lof
        from sklearn.neighbors import LocalOutlierFactor

        n_neighbors = min(20, max(1, len(valid) - 1))
        model = LocalOutlierFactor(n_neighbors=n_neighbors)
        pred = model.fit_predict(valid.values)

    flagged = valid.index[pred == -1]
    mask.loc[flagged] = True
    return mask


def detect_outliers(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    method: str = "iqr",
    k: float = _IQR_K,
    z_thresh: float = _Z_THRESH,
) -> OutlierResult:
    """지정한 방법으로 이상치를 탐지한다.

    columns 미지정 시 수치형 열 전체를 사용한다. sklearn 이 없으면 모델 기반
    방법은 자동으로 IQR 로 대체된다.
    """
    if columns is None:
        columns = list(df.select_dtypes(include="number").columns)
    columns = [c for c in columns if c in df.columns]
    if not columns:
        empty = pd.Series(False, index=df.index)
        return OutlierResult(method=method, columns=[], mask=empty, n_outliers=0)

    used = method
    if method in ("isolation_forest", "lof"):
        try:
            mask = _model_mask(df, columns, method)
        except ImportError:
            used = "iqr"
            mask = _iqr_mask(df, columns, k)
    elif method == "zscore":
        mask = _zscore_mask(df, columns, z_thresh)
    else:
        used = "iqr"
        mask = _iqr_mask(df, columns, k)

    return OutlierResult(
        method=used,
        columns=columns,
        mask=mask,
        n_outliers=int(mask.sum()),
    )
