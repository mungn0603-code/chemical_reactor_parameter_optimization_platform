"""reactor_platform.eda — AI 기반 EDA(탐색적 데이터 분석) Assistant.

설계 원칙(코어 엔진과 동일한 철학을 따른다)
--------------------------------------------
1) 계산 엔진과 분리: eda 패키지는 Reactor/Thermo/Kinetics 계산을 전혀 건드리지
   않는다. 데이터프레임(pandas)만 입력으로 받는 독립 모듈이다.
2) 자기설명: 모든 추천에는 반드시 '추천 이유(reason)'가 함께 붙는다.
3) 승인 기반: 전처리는 항상 사용자가 선택/승인해야 적용되며, 모든 변경은
   History 로 기록되어 Undo/Redo 가능하다.

모듈 구성
---------
- profile.py        : AI 데이터 프로파일링(구조·품질·통계 진단)
- outlier.py        : 이상치 탐지(IQR / Z-score / IsolationForest / LOF)
- recommendation.py : EDA 분석 후보 + 시각화 추천(규칙 기반, 이유 포함)
- visualization.py  : 추천 시각화 생성(plotly)
- preprocessing.py  : 전처리 이슈 탐지 + 보정 적용
- history.py        : Undo / Redo / 변경 이력 관리
- report.py         : EDA 보고서 자동 생성(Markdown / HTML)
- sample.py         : 데모용 반응기 데이터셋 생성
- ui.py             : Streamlit UI (streamlit 설치 시에만 임포트)
"""
from __future__ import annotations

from .history import HistoryManager, HistoryRecord
from .outlier import OutlierResult, detect_outliers
from .preprocessing import (
    PreprocessingSuggestion,
    apply_action,
    suggest_preprocessing,
)
from .profile import DataProfile, profile_dataframe
from .recommendation import (
    AnalysisRecommendation,
    VizRecommendation,
    recommend_analyses,
    recommend_visualizations,
)
from .report import build_report_html, build_report_markdown

__all__ = [
    "DataProfile",
    "profile_dataframe",
    "OutlierResult",
    "detect_outliers",
    "AnalysisRecommendation",
    "VizRecommendation",
    "recommend_analyses",
    "recommend_visualizations",
    "PreprocessingSuggestion",
    "suggest_preprocessing",
    "apply_action",
    "HistoryManager",
    "HistoryRecord",
    "build_report_markdown",
    "build_report_html",
]
