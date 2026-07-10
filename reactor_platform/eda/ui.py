"""eda/ui.py — AI 기반 EDA Assistant 의 Streamlit UI.

워크플로우(명세서 §12)
-----------------------
AI 추천 → EDA 추천 목록 → 사용자 선택 → 실행 → 자동 전처리 제안 → 승인 →
시각화 → Report 생성 (모든 전처리는 Undo 가능).

이 모듈은 streamlit 이 설치된 경우에만 임포트된다(코어/로직은 streamlit 무관).
render() 하나만 외부로 노출한다.
"""
from __future__ import annotations


import pandas as pd
import streamlit as st

from .history import HistoryManager
from .preprocessing import ACTION_LABELS, apply_action, suggest_preprocessing
from .profile import DataProfile, profile_dataframe
from .recommendation import (
    recommend_analyses,
    recommend_visualizations,
    top_recommendation_text,
)
from .report import build_report_html, build_report_markdown
from .sample import make_sample_dataset
from .visualization import build_figure

_USER = "user"


def render() -> None:
    """EDA Assistant 전체 화면을 그린다."""
    st.title("🔬 AI 기반 EDA Assistant")
    st.caption(
        "데이터를 올리면 AI 가 구조를 진단하고 · 분석/그래프를 추천하며 · "
        "승인 하에 전처리하고 · 모든 변경을 되돌릴 수 있습니다.")

    _load_section()
    if "eda_history" not in st.session_state:
        st.info("좌측에서 CSV 를 업로드하거나 '데모 데이터 사용'을 눌러 시작하세요.")
        return

    history: HistoryManager = st.session_state["eda_history"]
    df = history.current()
    profile = profile_dataframe(df)

    _profiling_section(profile)
    st.divider()
    _recommendation_section(profile)
    st.divider()
    _preprocessing_section(df, profile, history)
    st.divider()
    _visualization_section(history.current(), profile)
    st.divider()
    _history_section(history)
    st.divider()
    _report_section(profile_dataframe(history.current()), history)


# --------------------------------------------------------------------------- #
# 데이터 로드
# --------------------------------------------------------------------------- #
def _load_section() -> None:
    """CSV 업로드 / 데모 데이터 로드."""
    with st.sidebar:
        st.header("① 데이터")
        up = st.file_uploader("CSV 업로드", type=["csv"])
        col1, col2 = st.columns(2)
        if col1.button("데모 데이터 사용", use_container_width=True):
            _init_history(make_sample_dataset())
            st.rerun()
        if col2.button("초기화", use_container_width=True):
            for k in ("eda_history", "eda_source"):
                st.session_state.pop(k, None)
            st.rerun()
        if up is not None and st.session_state.get("eda_source") != up.name:
            try:
                df = pd.read_csv(up)
                _init_history(df, source=up.name)
                st.success(f"'{up.name}' 로드됨 · {df.shape[0]}행 {df.shape[1]}열")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"CSV 읽기 실패: {exc}")


def _init_history(df: pd.DataFrame, source: str = "sample") -> None:
    st.session_state["eda_history"] = HistoryManager(df, user=_USER)
    st.session_state["eda_source"] = source


# --------------------------------------------------------------------------- #
# 1. AI 데이터 프로파일링
# --------------------------------------------------------------------------- #
def _profiling_section(profile: DataProfile) -> None:
    st.header("1 · AI 데이터 프로파일링")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("행 / 열", f"{profile.n_rows} / {profile.n_cols}")
    c2.metric("데이터 품질 점수", f"{profile.quality_score:.0f} / 100")
    c3.metric("결측치", profile.total_missing)
    c4.metric("중복행", profile.n_duplicates)

    with st.expander("AI 요약 · 주요 발견 사항", expanded=True):
        for f in profile.findings:
            st.markdown(f"- {f}")

    with st.expander("열별 상세 진단"):
        rows = []
        for col in profile.columns:
            rows.append({
                "변수": col.name, "종류": col.kind, "자료형": col.dtype,
                "결측": col.n_missing, "고유값": col.n_unique,
                "평균": _r(col.mean), "표준편차": _r(col.std),
                "왜도": _r(col.skew), "첨도": _r(col.kurtosis),
                "이상치": col.n_outliers,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# 2. EDA 후보 추천 + 3/4. 시각화 추천
# --------------------------------------------------------------------------- #
def _recommendation_section(profile: DataProfile) -> list[str]:
    st.header("2 · AI 가 추천하는 EDA")
    st.success(f"💡 {top_recommendation_text(profile)}")

    analyses = recommend_analyses(profile)
    st.markdown("**분석 후보** (원하는 항목만 선택)")
    selected: list[str] = []
    cols = st.columns(2)
    for i, rec in enumerate(analyses):
        with cols[i % 2]:
            checked = st.checkbox(
                f"{rec.label}", value=rec.default_selected, key=f"an_{rec.key}",
                help=rec.reason)
            st.caption(f"↳ {rec.reason}")
            if checked:
                selected.append(rec.key)
    return selected


# --------------------------------------------------------------------------- #
# 5/6/7. 자동 전처리 제안 · 승인 · 적용
# --------------------------------------------------------------------------- #
def _preprocessing_section(
    df: pd.DataFrame, profile: DataProfile, history: HistoryManager
) -> None:
    st.header("3 · 자동 전처리 제안")
    suggestions = suggest_preprocessing(df, profile)
    if not suggestions:
        st.success("전처리가 필요한 문제가 발견되지 않았습니다. ✅")
        return

    st.caption("AI 가 탐지한 문제와 처리 방법입니다. 방법을 고르고 **적용**하면 즉시 반영되며 Undo 가능합니다.")
    for i, sug in enumerate(suggestions):
        label = sug.column or "(전체)"
        with st.container(border=True):
            st.markdown(f"**[{sug.issue}] {label}** — {sug.detail}")
            cc1, cc2 = st.columns([3, 1])
            choice = cc1.radio(
                "처리 방법", sug.options,
                index=sug.options.index(sug.recommended) if sug.recommended in sug.options else 0,
                format_func=lambda a: ACTION_LABELS.get(a, a),
                key=f"prep_{i}", horizontal=True)
            if cc2.button("적용", key=f"apply_{i}", use_container_width=True):
                new_df = apply_action(history.current(), choice, sug.column)
                desc = f"[{sug.issue}] {label} · {ACTION_LABELS.get(choice, choice)}"
                history.apply(new_df, desc, user=_USER)
                st.success(f"적용됨: {desc}")
                st.rerun()


# --------------------------------------------------------------------------- #
# 시각화 생성
# --------------------------------------------------------------------------- #
def _visualization_section(df: pd.DataFrame, profile: DataProfile) -> None:
    st.header("4 · AI 추천 시각화")
    vizzes = recommend_visualizations(profile)
    if not vizzes:
        st.info("추천할 시각화가 없습니다.")
        return

    labels = [f"{v.label} — {v.reason}" for v in vizzes]
    picked = st.multiselect(
        "그릴 그래프 선택", options=list(range(len(vizzes))),
        default=list(range(min(2, len(vizzes)))),
        format_func=lambda i: labels[i])

    made: list[str] = []
    for i in picked:
        v = vizzes[i]
        st.subheader(f"{v.label}")
        st.caption(f"추천 이유: {v.reason}")
        try:
            fig = build_figure(v.kind, df, columns=v.columns)
            st.plotly_chart(fig, use_container_width=True)
            made.append(v.label)
        except Exception as exc:  # noqa: BLE001
            st.warning(f"'{v.label}' 생성 실패: {exc}")
    st.session_state["eda_selected_charts"] = made


# --------------------------------------------------------------------------- #
# 8. Undo / Redo / History
# --------------------------------------------------------------------------- #
def _history_section(history: HistoryManager) -> None:
    st.header("5 · 변경 이력 (Undo / Redo)")
    c1, c2, c3 = st.columns([1, 1, 4])
    if c1.button("↶ Undo", disabled=not history.can_undo(), use_container_width=True):
        history.undo()
        st.rerun()
    if c2.button("↷ Redo", disabled=not history.can_redo(), use_container_width=True):
        history.redo()
        st.rerun()
    st.dataframe(history.history_table(), use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# 10. 보고서 자동 생성
# --------------------------------------------------------------------------- #
def _report_section(profile: DataProfile, history: HistoryManager) -> None:
    st.header("6 · 보고서 자동 생성")
    charts = st.session_state.get("eda_selected_charts", [])
    md = build_report_markdown(profile, history, charts)
    html = build_report_html(profile, history, charts)

    with st.expander("보고서 미리보기 (Markdown)"):
        st.markdown(md)

    c1, c2 = st.columns(2)
    c1.download_button("⬇ Markdown 다운로드", md, file_name="eda_report.md",
                       mime="text/markdown", use_container_width=True)
    c2.download_button("⬇ HTML 다운로드", html, file_name="eda_report.html",
                       mime="text/html", use_container_width=True)


def _r(x) -> str:
    return "-" if x is None else f"{x:.4g}"
