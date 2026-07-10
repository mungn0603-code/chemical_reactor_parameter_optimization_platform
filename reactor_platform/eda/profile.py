"""eda/profile.py — AI 데이터 프로파일링.

데이터프레임을 받아 구조·품질·통계 특성을 한 번에 진단한다. 결과(DataProfile)는
recommendation / preprocessing / report 모듈이 공통으로 사용하는 '단일 진단 원천'이다.

진단 항목
---------
변수 개수 / 행 개수 / 자료형 / 수치형·범주형·날짜형 분류 / 결측치 / 중복 /
이상치 / 상관관계 / 분포 특성(왜도·첨도) / 데이터 품질 점수.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

# 이상치 판정 기본 배수(Tukey fence). IQR 밖 1.5 배를 이상치로 본다.
_IQR_K = 1.5
# 강한 상관관계로 요약할 임계값.
_STRONG_CORR = 0.7


@dataclass
class ColumnProfile:
    """열(변수) 하나에 대한 진단 결과."""

    name: str
    dtype: str
    kind: str  # "numeric" | "categorical" | "datetime"
    n_missing: int
    missing_ratio: float
    n_unique: int
    # 수치형에서만 채워진다.
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    skew: Optional[float] = None
    kurtosis: Optional[float] = None
    n_outliers: int = 0
    n_negative: int = 0


@dataclass
class DataProfile:
    """데이터셋 전체 진단 결과."""

    n_rows: int
    n_cols: int
    columns: list[ColumnProfile]
    numeric_cols: list[str]
    categorical_cols: list[str]
    datetime_cols: list[str]
    n_duplicates: int
    total_missing: int
    quality_score: float
    correlation: Optional[pd.DataFrame] = None
    strong_pairs: list[tuple[str, str, float]] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    def column(self, name: str) -> ColumnProfile:
        """이름으로 열 프로파일을 찾는다."""
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    def summary_text(self) -> str:
        """사람이 읽는 한글 요약(자기설명)."""
        lines = [
            f"[데이터 프로파일] 행 {self.n_rows} · 열 {self.n_cols} "
            f"(수치형 {len(self.numeric_cols)} · 범주형 {len(self.categorical_cols)} "
            f"· 날짜형 {len(self.datetime_cols)})",
            f"  - 데이터 품질 점수: {self.quality_score:.1f} / 100",
            f"  - 결측치 총 {self.total_missing}개 · 중복행 {self.n_duplicates}개",
        ]
        for f in self.findings:
            lines.append(f"  - {f}")
        return "\n".join(lines)


def _classify_kind(series: pd.Series) -> str:
    """열의 종류를 numeric / categorical / datetime 으로 분류한다."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "categorical"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def _iqr_outlier_count(series: pd.Series, k: float = _IQR_K) -> int:
    """IQR(Tukey fence) 기준으로 이상치 개수를 센다."""
    s = series.dropna()
    if len(s) < 4:
        return 0
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lo = q1 - k * iqr
    hi = q3 + k * iqr
    return int(((s < lo) | (s > hi)).sum())


def _quality_score(
    n_rows: int,
    n_cols: int,
    total_missing: int,
    n_duplicates: int,
    total_outliers: int,
) -> float:
    """0~100 데이터 품질 점수. 결측·중복·이상치 비율만큼 감점한다."""
    if n_rows == 0 or n_cols == 0:
        return 0.0
    cells = n_rows * n_cols
    missing_ratio = total_missing / cells
    dup_ratio = n_duplicates / n_rows
    outlier_ratio = total_outliers / cells
    score = 100.0
    score -= missing_ratio * 100.0 * 1.0   # 결측치 비중
    score -= dup_ratio * 100.0 * 0.5        # 중복 비중(가중치 낮게)
    score -= outlier_ratio * 100.0 * 0.5    # 이상치 비중(가중치 낮게)
    return float(max(0.0, min(100.0, score)))


def profile_dataframe(df: pd.DataFrame) -> DataProfile:
    """데이터프레임을 진단해 DataProfile 을 만든다.

    입력 df 는 변경하지 않는다(읽기 전용).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("profile_dataframe 는 pandas DataFrame 을 받는다.")

    n_rows, n_cols = df.shape
    columns: list[ColumnProfile] = []
    numeric_cols: list[str] = []
    categorical_cols: list[str] = []
    datetime_cols: list[str] = []
    total_outliers = 0

    for name in df.columns:
        series = df[name]
        kind = _classify_kind(series)
        n_missing = int(series.isna().sum())
        missing_ratio = (n_missing / n_rows) if n_rows else 0.0
        n_unique = int(series.nunique(dropna=True))

        cp = ColumnProfile(
            name=str(name),
            dtype=str(series.dtype),
            kind=kind,
            n_missing=n_missing,
            missing_ratio=missing_ratio,
            n_unique=n_unique,
        )

        if kind == "numeric":
            numeric_cols.append(str(name))
            s = pd.to_numeric(series, errors="coerce").dropna()
            if len(s) > 0:
                cp.mean = float(s.mean())
                cp.std = float(s.std()) if len(s) > 1 else 0.0
                cp.min = float(s.min())
                cp.max = float(s.max())
                cp.skew = float(s.skew()) if len(s) > 2 else 0.0
                cp.kurtosis = float(s.kurt()) if len(s) > 3 else 0.0
                cp.n_outliers = _iqr_outlier_count(s)
                cp.n_negative = int((s < 0).sum())
                total_outliers += cp.n_outliers
        elif kind == "datetime":
            datetime_cols.append(str(name))
        else:
            categorical_cols.append(str(name))

        columns.append(cp)

    n_duplicates = int(df.duplicated().sum())
    total_missing = int(df.isna().sum().sum())

    correlation: Optional[pd.DataFrame] = None
    strong_pairs: list[tuple[str, str, float]] = []
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        correlation = corr
        seen: set[frozenset[str]] = set()
        for a in numeric_cols:
            for b in numeric_cols:
                if a == b:
                    continue
                key = frozenset((a, b))
                if key in seen:
                    continue
                r = corr.loc[a, b]
                if pd.notna(r) and abs(r) >= _STRONG_CORR:
                    strong_pairs.append((a, b, float(r)))
                    seen.add(key)
        strong_pairs.sort(key=lambda t: abs(t[2]), reverse=True)

    quality_score = _quality_score(
        n_rows, n_cols, total_missing, n_duplicates, total_outliers
    )

    findings = _build_findings(
        columns, strong_pairs, n_duplicates, n_rows
    )

    return DataProfile(
        n_rows=n_rows,
        n_cols=n_cols,
        columns=columns,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        datetime_cols=datetime_cols,
        n_duplicates=n_duplicates,
        total_missing=total_missing,
        quality_score=quality_score,
        correlation=correlation,
        strong_pairs=strong_pairs,
        findings=findings,
    )


def _build_findings(
    columns: list[ColumnProfile],
    strong_pairs: list[tuple[str, str, float]],
    n_duplicates: int,
    n_rows: int,
) -> list[str]:
    """AI 요약 문장(주요 발견 사항)을 생성한다."""
    out: list[str] = []

    for a, b, r in strong_pairs[:5]:
        direction = "양" if r > 0 else "음"
        strength = "매우 강한" if abs(r) >= 0.9 else "강한"
        out.append(f"{a} 와(과) {b} 은(는) {strength} {direction}의 상관관계를 보입니다 (r={r:.2f}).")

    for c in columns:
        if c.n_outliers > 0:
            out.append(f"{c.name} 변수에는 이상치가 {c.n_outliers}개 존재합니다.")
        if c.missing_ratio > 0:
            pct = c.missing_ratio * 100.0
            out.append(f"{c.name} 변수에 결측치 {c.n_missing}개({pct:.1f}%)가 있습니다.")
        if c.skew is not None and abs(c.skew) >= 1.0:
            side = "오른쪽" if c.skew > 0 else "왼쪽"
            out.append(
                f"{c.name} 분포는 {side}으로 치우쳐 있습니다 (왜도={c.skew:.2f}) → 로그 변환 검토."
            )
        if c.n_negative > 0 and c.kind == "numeric":
            out.append(f"{c.name} 에 음수 값 {c.n_negative}개가 있습니다(물리적으로 타당한지 확인).")

    if n_duplicates > 0:
        pct = (n_duplicates / n_rows * 100.0) if n_rows else 0.0
        out.append(f"완전 중복행이 {n_duplicates}개({pct:.1f}%) 발견되었습니다.")

    if not out:
        out.append("눈에 띄는 품질 문제가 발견되지 않았습니다. 분포·상관관계 탐색을 진행하세요.")
    return out
