"""eda/preprocessing.py — 자동 전처리 제안 + 보정 적용.

두 부분으로 나뉜다.
1) suggest_preprocessing(df, profile) : 문제를 탐지하고 수정 방법(선택지)을 제안.
2) apply_action(df, action)           : 사용자가 고른 방법을 '새 데이터프레임'에
   적용해 돌려준다(원본 불변 → History 스냅샷/Undo 가능).

절대 원본 df 를 제자리에서 바꾸지 않는다. 항상 복사본을 반환한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd

from .outlier import detect_outliers
from .profile import DataProfile


@dataclass
class PreprocessingSuggestion:
    """한 열(또는 데이터 전체)에 대한 전처리 제안."""

    issue: str          # "missing" | "duplicate" | "outlier" | "negative" | "skew" | "scale"
    column: Optional[str]
    detail: str         # 한글 설명(무엇이 문제인지)
    options: list[str]  # 사용자가 고를 수 있는 처리 방법(action 이름)
    recommended: str    # 기본 추천 방법
    severity: float = 0.5  # 0~1, 우선순위


# 각 이슈별 선택지(action 이름)와 한글 라벨.
ACTION_LABELS = {
    "impute_mean": "평균값 대체",
    "impute_median": "중앙값 대체",
    "impute_mode": "최빈값 대체",
    "drop_missing_rows": "결측행 삭제",
    "interpolate": "보간(선형)",
    "drop_duplicates": "중복행 삭제",
    "remove_outliers": "이상치 제거",
    "winsorize": "Winsorizing(경계값 캡)",
    "clip_negative": "음수 0으로 클립",
    "abs_negative": "절댓값 처리",
    "log_transform": "로그 변환",
    "normalize": "정규화(Min-Max)",
    "standardize": "표준화(Z-score)",
    "encode_onehot": "원-핫 인코딩",
    "encode_label": "라벨 인코딩",
    "keep": "유지(변경 없음)",
}


def suggest_preprocessing(
    df: pd.DataFrame, profile: Optional[DataProfile] = None
) -> list[PreprocessingSuggestion]:
    """데이터에서 전처리가 필요한 지점을 탐지하고 방법을 제안한다."""
    from .profile import profile_dataframe

    profile = profile or profile_dataframe(df)
    out: list[PreprocessingSuggestion] = []

    # 1) 중복행.
    if profile.n_duplicates > 0:
        out.append(PreprocessingSuggestion(
            "duplicate", None,
            f"완전 중복행이 {profile.n_duplicates}개 있습니다.",
            ["drop_duplicates", "keep"], "drop_duplicates",
            severity=0.7))

    # 2) 열별 이슈.
    for c in profile.columns:
        if c.n_missing > 0:
            if c.kind == "numeric":
                opts = ["impute_median", "impute_mean", "interpolate",
                        "drop_missing_rows", "keep"]
                rec = "impute_median"
            else:
                opts = ["impute_mode", "drop_missing_rows", "keep"]
                rec = "impute_mode"
            out.append(PreprocessingSuggestion(
                "missing", c.name,
                f"{c.name} 에 결측치 {c.n_missing}개({c.missing_ratio * 100:.1f}%) 발견.",
                opts, rec, severity=min(1.0, 0.5 + c.missing_ratio)))

        if c.kind == "numeric" and c.n_outliers > 0:
            out.append(PreprocessingSuggestion(
                "outlier", c.name,
                f"{c.name} 에 이상치 {c.n_outliers}개 발견(IQR 기준).",
                ["winsorize", "remove_outliers", "keep"], "winsorize",
                severity=0.6))

        if c.kind == "numeric" and c.n_negative > 0:
            out.append(PreprocessingSuggestion(
                "negative", c.name,
                f"{c.name} 에 음수 값 {c.n_negative}개(물리적으로 타당한지 확인).",
                ["keep", "clip_negative", "abs_negative"], "keep",
                severity=0.4))

        if (c.kind == "numeric" and c.skew is not None and c.skew >= 1.0
                and c.min is not None and c.min > 0):
            out.append(PreprocessingSuggestion(
                "skew", c.name,
                f"{c.name} 분포가 치우쳐 있습니다(왜도={c.skew:.2f}).",
                ["log_transform", "keep"], "log_transform", severity=0.4))

    # 3) 스케일 차이(정규화/표준화 제안).
    if len(profile.numeric_cols) >= 2:
        stds = [c.std for c in profile.columns if c.kind == "numeric" and c.std]
        if stds and max(stds) > 0 and (max(stds) / (min(stds) or 1e-9)) > 100:
            out.append(PreprocessingSuggestion(
                "scale", None,
                "변수 간 스케일 차이가 큽니다. 거리 기반 분석(PCA·클러스터링) 전 스케일 조정 권장.",
                ["standardize", "normalize", "keep"], "standardize", severity=0.5))

    out.sort(key=lambda s: s.severity, reverse=True)
    return out


def apply_action(
    df: pd.DataFrame, action: str, column: Optional[str] = None, **kwargs: Any
) -> pd.DataFrame:
    """전처리 action 을 새 데이터프레임에 적용해 반환한다(원본 불변)."""
    work = df.copy()

    if action == "keep":
        return work
    if action == "drop_duplicates":
        return work.drop_duplicates().reset_index(drop=True)

    if column is None:
        raise ValueError(f"'{action}' 에는 대상 column 이 필요합니다.")
    if column not in work.columns:
        raise KeyError(column)

    s = work[column]

    if action == "impute_mean":
        work[column] = s.fillna(pd.to_numeric(s, errors="coerce").mean())
    elif action == "impute_median":
        work[column] = s.fillna(pd.to_numeric(s, errors="coerce").median())
    elif action == "impute_mode":
        mode = s.mode(dropna=True)
        work[column] = s.fillna(mode.iloc[0] if len(mode) else s)
    elif action == "impute_value":
        work[column] = s.fillna(kwargs["value"])
    elif action == "interpolate":
        work[column] = pd.to_numeric(s, errors="coerce").interpolate(
            method="linear", limit_direction="both")
    elif action == "drop_missing_rows":
        work = work[work[column].notna()].reset_index(drop=True)
    elif action == "remove_outliers":
        res = detect_outliers(work, [column], method=kwargs.get("method", "iqr"))
        work = work[~res.mask].reset_index(drop=True)
    elif action == "winsorize":
        work[column] = _winsorize(pd.to_numeric(s, errors="coerce"),
                                  kwargs.get("k", 1.5))
    elif action == "clip_negative":
        work[column] = pd.to_numeric(s, errors="coerce").clip(lower=0)
    elif action == "abs_negative":
        work[column] = pd.to_numeric(s, errors="coerce").abs()
    elif action == "log_transform":
        num = pd.to_numeric(s, errors="coerce")
        work[column] = np.log1p(num.clip(lower=0))
    elif action == "normalize":
        num = pd.to_numeric(s, errors="coerce")
        rng = num.max() - num.min()
        work[column] = (num - num.min()) / (rng if rng else 1.0)
    elif action == "standardize":
        num = pd.to_numeric(s, errors="coerce")
        std = num.std()
        work[column] = (num - num.mean()) / (std if std else 1.0)
    elif action == "encode_label":
        work[column] = s.astype("category").cat.codes
    elif action == "encode_onehot":
        dummies = pd.get_dummies(s, prefix=column)
        work = pd.concat([work.drop(columns=[column]), dummies], axis=1)
    else:
        raise ValueError(f"알 수 없는 action: {action!r}")

    return work


def _winsorize(s: pd.Series, k: float = 1.5) -> pd.Series:
    """IQR 경계 밖 값을 경계값으로 캡(Winsorizing)한다."""
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return s
    lo, hi = q1 - k * iqr, q3 + k * iqr
    return s.clip(lower=lo, upper=hi)
