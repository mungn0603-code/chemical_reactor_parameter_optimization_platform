"""webui/dashboard.py — 통합 대시보드 라우터.

한 브라우저 안에서 홈(대시보드)과 세 기능을 오간다. 사이드바 버튼 또는 홈 화면의
카드를 클릭해 이동하며, 각 기능은 독립적으로 동작한다.
"""
from __future__ import annotations

import streamlit as st

from reactor_platform.eda.ui import render as render_eda

from . import reactor_view, report_view

_VIEWS = {
    "home": "🏠 대시보드",
    "reactor": "🧪 반응기 계산",
    "eda": "🔬 EDA Assistant",
    "report": "📄 보고서",
}


def _goto(view: str) -> None:
    st.session_state["view"] = view


def run() -> None:
    """대시보드 전체를 실행한다(진입 파일에서 호출)."""
    if "view" not in st.session_state:
        st.session_state["view"] = "home"

    with st.sidebar:
        st.markdown("### 메뉴")
        for key, label in _VIEWS.items():
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state["view"] == key else "secondary"):
                _goto(key)
                st.rerun()

    view = st.session_state["view"]
    if view == "home":
        _home()
    elif view == "reactor":
        reactor_view.render()
    elif view == "eda":
        render_eda()
    elif view == "report":
        report_view.render()


def _home() -> None:
    st.title("화학 반응기 파라미터 최적화 · 분석 플랫폼")
    st.caption("파라미터 주도 · 자기설명 · 계산 전 검증 — 반응기 계산부터 EDA·보고서까지 한 곳에서.")

    st.markdown("#### 기능 선택")
    cards = [
        ("reactor", "🧪 반응기 계산", "M1→M2→M3 순차 진행. 반응식을 입력하면 반응열·엔탈피가 "
                                   "교과서(Hess 법칙)대로 자동 계산·설정됩니다."),
        ("eda", "🔬 EDA Assistant", "데이터 품질 진단 → 분석/그래프 추천 → 승인 기반 전처리 → "
                                   "시각화 → 보고서. 모든 변경 Undo 가능."),
        ("report", "📄 통합 보고서", "반응·열역학·에너지수지 결과를 하나의 리포트로 묶어 "
                                  "텍스트·HTML 로 내려받습니다."),
    ]
    cols = st.columns(3)
    for col, (key, title, desc) in zip(cols, cards, strict=False):
        with col:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.write(desc)
                if st.button("이동 →", key=f"card_{key}", use_container_width=True):
                    _goto(key)
                    st.rerun()

    st.divider()
    st.markdown(
        "**학술적 활용**: 반응공학(반응속도론·열역학·에너지수지) 교과서 이론을 단계별로 "
        "확인하고, 실험/시뮬레이션 데이터를 EDA 로 분석해 보고서로 정리하는 교육·연구 워크플로우를 "
        "지원합니다.")
