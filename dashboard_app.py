"""dashboard_app.py — 통합 대시보드 진입 파일.

한 브라우저 안에서 반응기 계산(M1→M2→M3) · EDA Assistant · 통합 보고서를
카드/사이드바 클릭으로 오가는 단일 대시보드. 기존 진입 파일
(chemical_reactor_app.py, eda_assistant_app.py)과 계산 엔진은 변경하지 않는다.

실행:
    streamlit run dashboard_app.py
"""
from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Reactor Platform", page_icon="⚗️", layout="wide")
    from reactor_platform.webui.dashboard import run

    run()


if __name__ == "__main__":
    main()
