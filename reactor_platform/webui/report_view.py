"""webui/report_view.py — 통합 반응기 보고서 뷰.

M1→M2→M3 에서 계산한 반응/열역학/에너지 결과를 하나의 보고서로 묶어 화면에
보여주고 텍스트·HTML 로 내려받게 한다. (EDA 는 자체 보고서를 별도로 제공)
"""
from __future__ import annotations

import html as _html
from datetime import datetime

import streamlit as st

from reactor_platform.core.energy import EnergyBalance
from reactor_platform.core.reactors.cstr import CSTR
from reactor_platform.core.thermo import ThermoAnalyzer

from .registries import cstr_energy_registry, thermo_registry


def render() -> None:
    st.header("📄 통합 보고서")
    if "rx_inputs" not in st.session_state:
        st.info("먼저 **반응기 계산(M1→M2→M3)** 을 실행하면 여기서 통합 보고서를 생성할 수 있습니다.")
        return

    vals = st.session_state["rx_inputs"]
    rt = st.session_state.get("rx_thermo")
    eq = st.session_state.get("rx_reaction_eq", "-")

    try:
        cstr_report = CSTR(cstr_energy_registry(vals)).report()
        energy_report = EnergyBalance(cstr_energy_registry(vals)).report()
        thermo_report = ThermoAnalyzer(thermo_registry(vals)).report()
    except Exception as exc:  # noqa: BLE001
        st.error(f"보고서 생성 실패(입력을 확인하세요): {exc}")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.subheader("반응 요약")
    if rt is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ΔH°_rxn [kJ/mol]", f"{rt.dH_rxn:.2f}")
        c2.metric("ΔS°_rxn [J/mol·K]", f"{rt.dS_rxn:.2f}")
        c3.metric("ΔG° [kJ/mol]", f"{rt.dG_rxn:.2f}")
        c4.metric("K_eq", f"{rt.K_eq:.3g}")
        st.markdown(f"- 반응식: `{eq}` → **{rt.reaction.equation()}**")
        st.markdown(f"- 판정: {rt.enthalpy_label} · {rt.spontaneity_label}")
    else:
        st.caption("M2 열역학(반응식)을 실행하지 않아 표준상태 반응 요약이 없습니다.")

    text_report = _build_text(now, eq, rt, cstr_report, thermo_report, energy_report)
    html_report = _build_html(now, eq, rt, cstr_report, thermo_report, energy_report)

    with st.expander("보고서 미리보기 (텍스트)", expanded=True):
        st.code(text_report, language="text")

    d1, d2 = st.columns(2)
    d1.download_button("⬇ 텍스트(.txt) 다운로드", text_report,
                       file_name="reactor_report.txt", mime="text/plain",
                       use_container_width=True)
    d2.download_button("⬇ HTML 다운로드", html_report,
                       file_name="reactor_report.html", mime="text/html",
                       use_container_width=True)


def _build_text(now, eq, rt, cstr_r, thermo_r, energy_r) -> str:
    lines = [
        "==================================================",
        " 화학 반응기 통합 분석 보고서",
        f" 생성 시각: {now}",
        "==================================================",
        "",
        "[반응]",
        f"  입력 반응식: {eq}",
    ]
    if rt is not None:
        lines += [
            f"  균형 반응식: {rt.reaction.equation()}  (원소균형 {'OK' if rt.balanced else '불균형'})",
            f"  ΔH°_rxn = {rt.dH_rxn:.3f} kJ/mol ({rt.enthalpy_label})",
            f"  ΔS°_rxn = {rt.dS_rxn:.3f} J/mol·K",
            f"  ΔG°(T={rt.T:.2f}K) = {rt.dG_rxn:.3f} kJ/mol ({rt.spontaneity_label})",
            f"  K_eq = {rt.K_eq:.4g}",
            "  [Hess 법칙 유도]",
        ] + [f"    {s}" for s in rt.steps]
    lines += ["", "──────────  M1 · CSTR  ──────────", cstr_r,
              "", "──────────  M2 · 열역학  ──────────", thermo_r,
              "", "──────────  M3 · 에너지수지  ──────────", energy_r]
    return "\n".join(lines)


def _build_html(now, eq, rt, cstr_r, thermo_r, energy_r) -> str:
    def esc(x: str) -> str:
        return _html.escape(x)

    rxn_html = f"<p><b>입력 반응식:</b> <code>{esc(eq)}</code></p>"
    if rt is not None:
        steps = "".join(f"<li>{esc(s)}</li>" for s in rt.steps)
        rxn_html += (
            f"<p><b>균형 반응식:</b> {esc(rt.reaction.equation())} "
            f"({'원소균형 ✓' if rt.balanced else '⚠ 불균형'})</p>"
            f"<table><tr><th>ΔH°_rxn</th><th>ΔS°_rxn</th><th>ΔG°</th><th>K_eq</th></tr>"
            f"<tr><td>{rt.dH_rxn:.3f} kJ/mol</td><td>{rt.dS_rxn:.3f} J/mol·K</td>"
            f"<td>{rt.dG_rxn:.3f} kJ/mol</td><td>{rt.K_eq:.4g}</td></tr></table>"
            f"<p>판정: {esc(rt.enthalpy_label)} · {esc(rt.spontaneity_label)}</p>"
            f"<p><b>Hess 법칙 유도:</b></p><ol>{steps}</ol>")

    def block(title, body):
        return f"<h2>{esc(title)}</h2><pre>{esc(body)}</pre>"

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>반응기 통합 보고서</title>
<style>
 body {{ font-family:-apple-system,'Segoe UI',Roboto,sans-serif; max-width:960px;
        margin:2rem auto; padding:0 1rem; color:#202124; line-height:1.6; }}
 h1 {{ color:#1a73e8; border-bottom:2px solid #1a73e8; padding-bottom:.3rem; }}
 h2 {{ color:#174ea6; margin-top:1.6rem; }}
 pre {{ background:#f1f3f4; padding:1rem; border-radius:6px; overflow-x:auto;
        white-space:pre-wrap; font-size:.85rem; }}
 table {{ border-collapse:collapse; margin:1rem 0; }}
 th,td {{ border:1px solid #dadce0; padding:6px 12px; }} th {{ background:#e8f0fe; }}
 code {{ background:#f1f3f4; padding:1px 4px; border-radius:3px; }}
</style></head><body>
<h1>화학 반응기 통합 분석 보고서</h1>
<p><em>생성 시각: {esc(now)}</em></p>
<h2>반응</h2>{rxn_html}
{block("M1 · CSTR", cstr_r)}
{block("M2 · 열역학", thermo_r)}
{block("M3 · 에너지수지", energy_r)}
</body></html>"""
