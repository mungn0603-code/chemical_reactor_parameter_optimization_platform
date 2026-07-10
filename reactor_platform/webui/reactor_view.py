"""webui/reactor_view.py — M1→M2→M3 순차 반응기 계산 뷰.

흐름
----
M1 반응속도론/CSTR : A·Ea·T·n·C_A0·v0·V → Arrhenius k, 체류시간 τ, 전환율 X
        ↓ (온도 T 이월)
M2 열역학          : 반응식 입력 → 화학종 매핑 → Hess 법칙으로 ΔH°·ΔS° 자동 설정
                     → dG, K_eq, 자발성 판정   (반응열/엔탈피가 '자동으로 세팅'됨)
        ↓ (반응열 ΔH_rxn 이월)
M3 에너지수지      : dH_rxn(자동) → 열부하 Q, 가열/냉각 판정

계산은 전부 기존 엔진(CSTR·ThermoAnalyzer·EnergyBalance)을 그대로 호출한다.
"""
from __future__ import annotations

import streamlit as st

from reactor_platform.core.energy import EnergyBalance
from reactor_platform.core.reactions import (
    REACTION_LIBRARY,
    ReactionError,
    analyze_reaction,
    element_balance,
    reaction_kinetics,
)
from reactor_platform.core.reactors.cstr import CSTR
from reactor_platform.core.thermo import ThermoAnalyzer

from .registries import cstr_energy_registry, thermo_registry

_STEPS = ["M1 · 반응속도론/CSTR", "M2 · 열역학", "M3 · 에너지수지"]

_DEFAULT_INPUTS = dict(
    A=1_000_000.0, Ea=50.0, T=80.0, n=1.0, C_A0=2.0, v0=10.0, V=100.0,
    cp_flow=500.0, T_feed=25.0,
    # 열역학 기본값(반응식 선택 전). 반응식을 고르면 자동 덮어씀.
    dH=-50.0, dS=80.0, dH_rxn=-80.0,
)


def _state() -> dict:
    """세션에 저장된 반응기 입력값(없으면 기본값)."""
    if "rx_inputs" not in st.session_state:
        st.session_state["rx_inputs"] = dict(_DEFAULT_INPUTS)
    return st.session_state["rx_inputs"]


def render() -> None:
    """반응기 계산 뷰 전체를 그린다."""
    st.header("🧪 반응기 계산 · M1 → M2 → M3")
    st.caption("반응식을 고르면 M1 에서는 반응속도 파라미터(A·Ea·차수, 문헌 대표값)가, "
               "M2 에서는 반응 엔탈피·엔트로피(Hess 법칙 계산)가 자동 반영됩니다.")

    vals = _state()
    step = st.radio("단계", _STEPS, horizontal=True, label_visibility="collapsed")
    st.progress((_STEPS.index(step) + 1) / len(_STEPS))

    if step == _STEPS[0]:
        _step_m1(vals)
    elif step == _STEPS[1]:
        _step_m2(vals)
    else:
        _step_m3(vals)


# --------------------------------------------------------------------------- #
# 공유 반응 선택기 (M1·M2 가 같은 반응을 사용하도록 세션에 저장)
# --------------------------------------------------------------------------- #
def _pick_reaction(widget_key: str) -> tuple[str, str]:
    """대표 반응 선택 위젯. (선택 이름, 반응식) 반환. 선택은 세션에 저장돼 M1·M2 공유."""
    names = ["(직접 입력)"] + [nr.name for nr in REACTION_LIBRARY]
    stored = st.session_state.get("rx_reaction_name", REACTION_LIBRARY[0].name)
    idx = names.index(stored) if stored in names else 0
    choice = st.selectbox("대표 반응 선택", names, index=idx, key=widget_key,
                          help="교과서 대표 반응을 고르거나 직접 반응식을 입력하세요.")
    st.session_state["rx_reaction_name"] = choice
    if choice == "(직접 입력)":
        default_eq = st.session_state.get("rx_reaction_eq", "N2 + 3 H2 -> 2 NH3")
        eq = st.text_input("반응식 입력", value=default_eq, key=widget_key + "_eq",
                           help="예: N2 + 3 H2 -> 2 NH3  ·  CH4 + 2 O2 -> CO2 + 2 H2O(g)")
    else:
        nr = next(n for n in REACTION_LIBRARY if n.name == choice)
        eq = nr.equation
        st.caption(f"선택: `{nr.equation}` — {nr.note}")
    st.session_state["rx_reaction_eq"] = eq
    return choice, eq


# --------------------------------------------------------------------------- #
# M1 · 반응속도론 / CSTR
# --------------------------------------------------------------------------- #
def _step_m1(vals: dict) -> None:
    st.subheader("M1 · 반응속도론 & 등온 CSTR")

    st.markdown("**반응 선택** — 반응을 고르면 빈도인자 A·활성화에너지 Ea·반응차수가 "
                "문헌 대표값으로 자동 반영됩니다.")
    name, _eq = _pick_reaction("m1_rxn")
    kin = reaction_kinetics(name)

    auto = False
    if kin is not None:
        manual = st.checkbox("A·Ea·차수를 직접 수정(수동 입력)", value=False, key="m1_manual")
        auto = not manual
        if auto:
            vals["A"], vals["Ea"], vals["n"] = kin.A, kin.Ea, kin.order
            st.success(f"반응속도 자동 반영: A = {kin.A:.3g} 1/s · Ea = {kin.Ea:g} kJ/mol · "
                       f"n = {kin.order:g}")
            st.caption(f"↳ 출처: {kin.source}  ·  ⚠ A·Ea 는 반응식에서 유도되는 값이 아니라 "
                       "촉매·조건에 따라 달라지는 **실험값(대표 스케일)** 입니다.")
    else:
        st.info("이 반응의 문헌 반응속도(A·Ea) 데이터가 없어 아래에서 직접 입력합니다.")

    c1, c2, c3 = st.columns(3)
    vals["A"] = c1.number_input("빈도인자 A [1/s]", value=float(vals["A"]),
                                format="%.6g", disabled=auto)
    vals["Ea"] = c2.number_input("활성화에너지 Ea [kJ/mol]", value=float(vals["Ea"]),
                                 disabled=auto)
    vals["T"] = c3.slider("반응온도 T [°C]", -50.0, 400.0, float(vals["T"]))
    vals["n"] = c1.number_input("반응차수 n [-]", value=float(vals["n"]),
                                min_value=0.0, max_value=3.0, step=1.0, disabled=auto)
    vals["C_A0"] = c2.number_input("초기농도 C_A0 [mol/L]", value=float(vals["C_A0"]), min_value=0.0)
    vals["v0"] = c3.number_input("부피유량 v0 [L/min]", value=float(vals["v0"]), min_value=0.0)
    vals["V"] = c1.number_input("반응기부피 V [L]", value=float(vals["V"]), min_value=0.0)

    try:
        res = CSTR(cstr_energy_registry(vals)).solve()
    except Exception as exc:  # noqa: BLE001
        st.error(f"입력 검증 실패: {exc}")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("전환율 X", f"{res.values['X']:.3f}")
    m2.metric("속도상수 k [1/s]", f"{res.values['k']:.4g}")
    m3.metric("체류시간 τ [s]", f"{res.values['tau']:.4g}")
    with st.expander("계산 리포트 (자기설명)"):
        st.code(CSTR(cstr_energy_registry(vals)).report(res), language="text")
    st.info("✅ M1 완료. 상단에서 **M2 · 열역학** 으로 진행하세요.")


# --------------------------------------------------------------------------- #
# M2 · 열역학 (반응식 → 자동 ΔH°·ΔS°)
# --------------------------------------------------------------------------- #
def _step_m2(vals: dict) -> None:
    st.subheader("M2 · 열역학 (반응식 입력 → 자동 설정)")
    st.caption("M1 과 같은 반응식을 사용합니다. 여기서 바꾸면 M1 의 반응속도도 함께 바뀝니다.")

    _name, eq = _pick_reaction("m2_rxn")

    T_abs = float(vals["T"]) + 273.15
    try:
        rt = analyze_reaction(eq, T=T_abs)
    except ReactionError as exc:
        st.error(f"반응식 오류: {exc}")
        return

    st.session_state["rx_reaction_eq"] = eq
    st.session_state["rx_thermo"] = rt

    balanced, residual = element_balance(rt.reaction)
    if not balanced:
        st.warning(f"⚠ 원소 균형이 맞지 않습니다(잔차 {residual}). 계수를 확인하세요. "
                   "계산은 진행하지만 물리적으로 타당하지 않을 수 있습니다.")
    else:
        st.success(f"균형 반응식: **{rt.reaction.equation()}**  (원소 균형 ✓)")

    # Hess 법칙으로 자동 계산된 값을 열역학 입력에 '자동 설정'.
    vals["dH"] = round(rt.dH_rxn, 4)
    vals["dS"] = round(rt.dS_rxn, 4)
    vals["dH_rxn"] = round(rt.dH_rxn, 4)

    a, b, c, d = st.columns(4)
    a.metric("ΔH°_rxn [kJ/mol]", f"{rt.dH_rxn:.2f}", help=rt.enthalpy_label)
    b.metric("ΔS°_rxn [J/mol·K]", f"{rt.dS_rxn:.2f}")
    c.metric(f"ΔG°(T={T_abs:.1f}K) [kJ/mol]", f"{rt.dG_rxn:.2f}", help=rt.spontaneity_label)
    d.metric("K_eq", f"{rt.K_eq:.3g}")

    st.markdown(f"판정: **{rt.enthalpy_label}** · **{rt.spontaneity_label}** "
                f"(ΔH°, ΔS° 는 298.15 K 표준값, ΔG=ΔH°−TΔS°)")

    with st.expander("Hess 법칙 유도 과정 (교과서 이론)", expanded=True):
        for s in rt.steps:
            st.markdown(f"- {s}")

    # 자동 설정된 dH·dS 로 기존 ThermoAnalyzer 를 그대로 실행(교차 검증).
    with st.expander("열역학 엔진 리포트 (ThermoAnalyzer)"):
        try:
            st.code(ThermoAnalyzer(thermo_registry(vals)).report(), language="text")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"ThermoAnalyzer 실행 경고: {exc}")

    st.info("✅ M2 완료 — 반응열 ΔH_rxn 이 자동 설정되었습니다. 상단에서 **M3 · 에너지수지** 로 진행하세요.")


# --------------------------------------------------------------------------- #
# M3 · 에너지수지
# --------------------------------------------------------------------------- #
def _step_m3(vals: dict) -> None:
    st.subheader("M3 · CSTR 에너지수지")
    if "rx_thermo" in st.session_state:
        st.caption(f"M2 에서 자동 설정된 반응열 ΔH_rxn = **{vals['dH_rxn']:.2f} kJ/mol** "
                   f"(반응: `{st.session_state.get('rx_reaction_eq', '-')}`)")
    else:
        st.caption("M2 를 먼저 진행하면 반응열이 자동 설정됩니다. (지금은 기본값 사용)")

    c1, c2 = st.columns(2)
    vals["cp_flow"] = c1.number_input("공급 열용량유량 cp_flow [W/K]",
                                      value=float(vals["cp_flow"]), min_value=0.0)
    vals["T_feed"] = c2.slider("공급온도 T_feed [°C]", -50.0, 400.0, float(vals["T_feed"]))

    try:
        eres = EnergyBalance(cstr_energy_registry(vals)).solve()
    except Exception as exc:  # noqa: BLE001
        st.error(f"입력 검증 실패: {exc}")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric(f"열부하 Q [kW] · {eres.duty}", f"{eres.values['Q'] / 1000:.2f}")
    m2.metric("반응열항 [kW]", f"{eres.values['Q_reaction'] / 1000:.2f}")
    m3.metric("현열항 [kW]", f"{eres.values['Q_sensible'] / 1000:.2f}")
    with st.expander("계산 리포트 (자기설명)"):
        st.code(EnergyBalance(cstr_energy_registry(vals)).report(eres), language="text")
    st.success("✅ M1→M2→M3 완료. 상단 사이드바에서 **보고서** 로 이동해 통합 리포트를 받으세요.")
