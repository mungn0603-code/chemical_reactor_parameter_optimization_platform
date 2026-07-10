"""eda_assistant_app.py — AI 기반 EDA Assistant 진입 파일.

기존 `chemical_reactor_app.py`(반응기 계산 콘솔)와 완전히 분리된 독립 앱이다.
계산 엔진/열역학/속도론/ParameterRegistry 는 전혀 변경하지 않는다.

실행:
    streamlit run eda_assistant_app.py
"""
from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="EDA Assistant", page_icon="🔬", layout="wide")
    # streamlit 이 있을 때만 UI 를 임포트한다(로직 모듈은 streamlit 무관).
    from reactor_platform.eda.ui import render

    render()


if __name__ == "__main__":
    main()
