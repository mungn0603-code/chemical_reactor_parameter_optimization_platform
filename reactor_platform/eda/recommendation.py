"""eda/recommendation.py — AI EDA 추천 엔진(규칙 기반).

데이터 특성(DataProfile)을 근거로 (1) 어떤 분석을 할지, (2) 어떤 그래프를 그릴지를
'이유(reason)와 함께' 추천한다. 단순 나열이 아니라 데이터에 맞춰 우선순위를 매긴다.

왜 규칙 기반인가
----------------
- 결정적(deterministic)이고 재현 가능하며, 외부 API/키가 필요 없다.
- 추천 근거가 항상 명시되어 프로젝트의 '자기설명' 원칙에 맞는다.
- 동일한 인터페이스로 나중에 LLM 백엔드를 끼울 수 있다(향후 AI Optimization 연계).
"""
from __future__ import annotations

from dataclasses import dataclass

from .profile import DataProfile

# 반응공학 도메인 힌트: 이런 이름의 열이 있으면 특화 분석을 추천한다.
_DOMAIN_KEYS = {
    "temperature": ["temperature", "temp", "t_", "온도"],
    "pressure": ["pressure", "press", "압력"],
    "conversion": ["conversion", "x", "전환"],
    "yield": ["yield", "수율"],
    "residence": ["residence", "tau", "체류"],
    "activation": ["activation", "ea", "활성화"],
    "profit": ["profit", "revenue", "cost", "경제", "이익"],
}


@dataclass
class AnalysisRecommendation:
    """분석 후보 하나(체크박스 항목)."""

    key: str
    label: str
    reason: str
    score: float  # 0~1, 클수록 강한 추천
    default_selected: bool = False


@dataclass
class VizRecommendation:
    """시각화 후보 하나."""

    kind: str          # visualization.build_figure 의 kind 와 일치
    label: str
    reason: str
    columns: list[str]
    score: float


def _has_domain(profile: DataProfile, key: str) -> list[str]:
    """도메인 키워드에 매칭되는 열 이름을 찾는다."""
    tokens = _DOMAIN_KEYS.get(key, [])
    hits = []
    for c in profile.numeric_cols:
        low = c.lower()
        if any(tok in low for tok in tokens):
            hits.append(c)
    return hits


def recommend_analyses(profile: DataProfile) -> list[AnalysisRecommendation]:
    """데이터 특성에 맞는 EDA 분석 후보를 우선순위와 함께 추천한다."""
    recs: list[AnalysisRecommendation] = []
    n_num = len(profile.numeric_cols)
    n_cat = len(profile.categorical_cols)
    n_dt = len(profile.datetime_cols)

    # 항상 유용한 기본 분석.
    recs.append(AnalysisRecommendation(
        "summary", "데이터 요약", "데이터 구조와 자료형을 먼저 파악하는 것이 모든 EDA 의 출발점입니다.",
        0.95, True))
    recs.append(AnalysisRecommendation(
        "basic_stats", "기초 통계", "평균·표준편차·분위수로 각 변수의 스케일과 분포를 확인합니다.",
        0.9, True))

    if n_num >= 1:
        recs.append(AnalysisRecommendation(
            "distribution", "변수 분포", "수치형 변수가 있어 분포(치우침·다봉성) 확인이 유용합니다.",
            0.85, True))

    # 이상치가 실제로 있으면 강하게 추천.
    total_out = sum(c.n_outliers for c in profile.columns)
    if total_out > 0:
        recs.append(AnalysisRecommendation(
            "outlier", "이상치 분석",
            f"이상치가 총 {total_out}개 탐지되어 분석 전 처리 여부 판단이 필요합니다.",
            0.9, True))
    elif n_num >= 1:
        recs.append(AnalysisRecommendation(
            "outlier", "이상치 분석", "수치형 변수의 극단값 존재 여부를 점검합니다.", 0.5, False))

    if n_num >= 2:
        strong = len(profile.strong_pairs)
        score = 0.9 if strong else 0.7
        reason = (
            f"강한 상관 쌍이 {strong}개 있어 변수 관계 분석이 특히 유용합니다."
            if strong else "수치형 변수가 2개 이상이라 상관관계를 볼 수 있습니다."
        )
        recs.append(AnalysisRecommendation("correlation", "상관관계 분석", reason, score, strong > 0))
        recs.append(AnalysisRecommendation(
            "multicollinearity", "다중공선성",
            "상관이 높은 변수쌍이 있으면 회귀·모델링 전 다중공선성 점검이 필요합니다.",
            0.6 if strong else 0.4, False))

    if n_num >= 3:
        recs.append(AnalysisRecommendation(
            "pca", "PCA(주성분분석)",
            f"수치형 변수가 {n_num}개로 많아 차원 축소로 구조를 요약할 수 있습니다.",
            0.65, False))
        recs.append(AnalysisRecommendation(
            "clustering", "클러스터링",
            "다변량 데이터에서 운전조건 군집(레짐)을 자동으로 찾습니다.", 0.55, False))
        recs.append(AnalysisRecommendation(
            "sensitivity", "민감도 분석",
            "출력변수(전환율·수율 등)에 각 입력이 미치는 영향의 크기를 비교합니다.",
            0.6, False))

    if n_dt >= 1:
        recs.append(AnalysisRecommendation(
            "timeseries", "시계열 분석", "날짜형 변수가 있어 시간에 따른 변화 추이를 볼 수 있습니다.",
            0.75, True))

    if n_cat >= 1:
        recs.append(AnalysisRecommendation(
            "group_compare", "그룹/시나리오 비교",
            "범주형 변수 기준으로 그룹 간 성능 차이를 비교할 수 있습니다.", 0.6, False))

    # 도메인 특화 추천(반응공학).
    _append_domain_analyses(profile, recs)

    recs.sort(key=lambda r: r.score, reverse=True)
    return recs


def _append_domain_analyses(
    profile: DataProfile, recs: list[AnalysisRecommendation]
) -> None:
    """반응기 도메인에 특화된 분석을 조건부로 추가한다."""
    temp = _has_domain(profile, "temperature")
    conv = _has_domain(profile, "conversion")
    yld = _has_domain(profile, "yield")
    press = _has_domain(profile, "pressure")
    res = _has_domain(profile, "residence")
    act = _has_domain(profile, "activation")
    profit = _has_domain(profile, "profit")

    if temp and conv:
        recs.append(AnalysisRecommendation(
            "temp_effect", "Temperature 영향",
            f"{temp[0]} 와 {conv[0]} 관계는 Arrhenius 거동 확인의 핵심입니다.", 0.85, True))
        recs.append(AnalysisRecommendation(
            "conversion_trend", "Conversion 변화",
            f"운전조건에 따른 {conv[0]} 변화를 추적합니다.", 0.8, False))
    if yld:
        recs.append(AnalysisRecommendation(
            "yield_trend", "Yield 변화", f"{yld[0]} 의 조건별 변화를 분석합니다.", 0.75, False))
    if press:
        recs.append(AnalysisRecommendation(
            "pressure_effect", "Pressure 영향", f"{press[0]} 가 성능에 미치는 영향을 확인합니다.",
            0.7, False))
    if res:
        recs.append(AnalysisRecommendation(
            "residence_effect", "Residence Time 영향",
            f"{res[0]} 와 전환율의 관계(체류시간 효과)를 봅니다.", 0.7, False))
    if act:
        recs.append(AnalysisRecommendation(
            "activation_effect", "Activation Energy 영향",
            f"{act[0]} 가 속도상수·전환율에 미치는 민감도를 봅니다.", 0.65, False))
    if profit:
        recs.append(AnalysisRecommendation(
            "economics", "경제성 비교", "이익·비용 변수 기준으로 시나리오 경제성을 비교합니다.",
            0.7, False))


def recommend_visualizations(profile: DataProfile) -> list[VizRecommendation]:
    """데이터 특성에 맞는 시각화를 이유와 함께 추천한다."""
    recs: list[VizRecommendation] = []
    num = profile.numeric_cols
    cat = profile.categorical_cols
    dt = profile.datetime_cols

    # 분포: 치우친 변수를 우선.
    if num:
        skewed = [c.name for c in profile.columns
                  if c.kind == "numeric" and c.skew is not None and abs(c.skew) >= 1.0]
        target = skewed[0] if skewed else num[0]
        reason = ("치우친 분포를 확인하기에 좋습니다." if skewed
                  else "각 수치형 변수의 분포를 확인하는 기본 그래프입니다.")
        recs.append(VizRecommendation("histogram", "Histogram", reason, [target], 0.8))

    # 상관관계 기반 산점도 + 히트맵.
    if profile.strong_pairs:
        a, b, r = profile.strong_pairs[0]
        recs.append(VizRecommendation(
            "scatter", "Scatter Plot",
            f"{a} 와 {b} 는 강한 상관(r={r:.2f})을 보여 관계 확인에 적합합니다.",
            [a, b], 0.95))
    elif len(num) >= 2:
        recs.append(VizRecommendation(
            "scatter", "Scatter Plot", "두 수치형 변수의 관계를 확인합니다.", num[:2], 0.6))

    if len(num) >= 2:
        recs.append(VizRecommendation(
            "correlation_heatmap", "Correlation Heatmap",
            "여러 변수 간 상관 구조를 한눈에 봅니다.", num, 0.85))
    if 3 <= len(num) <= 8:
        recs.append(VizRecommendation(
            "pair_plot", "Pair Plot", "전체 수치형 변수의 관계를 격자로 살펴봅니다.", num, 0.6))

    # 이상치 시각화.
    has_out = any(c.n_outliers > 0 for c in profile.columns)
    if num:
        recs.append(VizRecommendation(
            "box", "Box Plot",
            ("이상치가 탐지되어 상자그림으로 극단값을 확인하는 것을 추천합니다."
             if has_out else "사분위와 극단값을 확인합니다."),
            num, 0.85 if has_out else 0.5))
    if cat and num:
        recs.append(VizRecommendation(
            "violin", "Violin Plot",
            f"{cat[0]} 그룹별 {num[0]} 분포를 비교합니다.", [cat[0], num[0]], 0.55))

    # 시계열.
    if dt and num:
        recs.append(VizRecommendation(
            "line", "Line Plot", f"{dt[0]} 기준 {num[0]} 의 시간 변화를 봅니다.",
            [dt[0], num[0]], 0.8))

    # 3D / 등고선(반응기 특화).
    temp = _has_domain(profile, "temperature")
    press = _has_domain(profile, "pressure")
    conv = _has_domain(profile, "conversion")
    if temp and press and conv:
        cols = [temp[0], press[0], conv[0]]
        recs.append(VizRecommendation(
            "surface_3d", "3D Surface", "Temperature-Pressure-Conversion 반응표면을 봅니다.",
            cols, 0.75))
        recs.append(VizRecommendation(
            "contour", "Contour Plot", "등고선으로 최적 운전 조건 영역을 탐색합니다.", cols, 0.7))

    # 다변량 비교.
    if len(num) >= 3:
        recs.append(VizRecommendation(
            "parallel", "Parallel Coordinates", "여러 변수를 동시에 비교합니다.", num, 0.5))
    if cat and len(num) >= 3:
        recs.append(VizRecommendation(
            "radar", "Radar Chart", f"{cat[0]} 별 성능 지표를 방사형으로 비교합니다.",
            [cat[0]] + num[:5], 0.5))

    # 범주형만 있는 경우.
    if cat and not num:
        recs.append(VizRecommendation(
            "count", "Count Plot", "데이터가 범주형이므로 범주별 빈도를 봅니다.", [cat[0]], 0.7))

    recs.sort(key=lambda r: r.score, reverse=True)
    return recs


def top_recommendation_text(profile: DataProfile) -> str:
    """가장 유용한 추천을 한 문장으로 요약(자동 추천 메시지)."""
    vizzes = recommend_visualizations(profile)
    if not vizzes:
        if profile.categorical_cols:
            return "데이터가 범주형이므로 Count Plot 을 추천합니다."
        return "추천할 시각화가 없습니다. 데이터를 확인하세요."
    top = [v.label for v in vizzes[:2]]
    if len(top) == 1:
        return f"현재 데이터에서는 {top[0]} 이(가) 가장 유용합니다."
    return f"현재 데이터에서는 {top[0]} 와(과) {top[1]} 이(가) 가장 유용합니다."
