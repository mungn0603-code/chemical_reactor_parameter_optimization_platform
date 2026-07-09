"""chemical_reactor_app.py - 반응기 플랫폼 웹 콘솔 (정식 진입 파일).

명명 규칙: 레포별로 <주제>_app.py 형태의 고유 이름을 쓴다.

실행:
    streamlit run chemical_reactor_app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from reactor_platform.core.energy import EnergyBalance
from reactor_platform.core.reactors.cstr import CSTR
from reactor_platform.core.scenario_lab import Economics
from reactor_platform.core.thermo import ThermoAnalyzer
from reactor_platform.parameters.registry import ParameterRegistry
from reactor_platform.parameters.schema import Parameter, Role

# --- 계산 로직 (스트림릿과 무관하게 재사용 가능) ---------------------------


def _reg(rows: list[tuple]) -> ParameterRegistry:
    reg = ParameterRegistry()
    for key, label, sym, unit, role, desc, val, mn, mx in rows:
        reg.add(Parameter(key, label, sym, unit, role, desc, value=val, min=mn, max=mx))
    return reg


def cstr_energy_registry(v: dict) -> ParameterRegistry:
    """CSTR + 에너지 입력으로 레지스트리를 만든다."""
    return _reg([
        ("pre_exponential", "빈도인자", "A", "1/s", Role.INPUT, "빈도인자", v["A"], 0, None),
        ("activation_energy", "활성화에너지", "Ea", "kJ/mol", Role.INPUT, "장벽", v["Ea"], 0, 500),
        ("temperature", "반응온도", "T", "degC", Role.INPUT, "운전온도", v["T"], -273.15, None),
        ("reaction_order", "반응차수", "n", "-", Role.INPUT, "지수", v["n"], 0, 3),
        ("C_A0", "초기농도", "C_A0", "mol/L", Role.INPUT, "입구농도", v["C_A0"], 0, None),
        ("v0", "부피유량", "v0", "L/min", Role.INPUT, "유량", v["v0"], 0, None),
        ("volume", "반응기부피", "V", "L", Role.INPUT, "부피", v["V"], 0, None),
        ("R", "기체상수", "R", "J/mol", Role.CONSTANT, "상수", 8.314462618, None, None),
        ("dH_rxn", "반응열", "dH_rxn", "kJ/mol", Role.INPUT, "반응열", v["dH_rxn"], -2000, 2000),
        ("cp_flow", "열용량유량", "cp_flow", "W/K", Role.INPUT, "현열", v["cp_flow"], 0, None),
        ("T_feed", "공급온도", "T_feed", "degC", Role.INPUT, "공급온도", v["T_feed"], -273.15, None),
        ("k", "속도상수", "k", "1/s", Role.DERIVED, "결과", None, None, None),
        ("tau", "체류시간", "tau", "s", Role.DERIVED, "결과", None, None, None),
        ("X", "전환율", "X", "-", Role.DERIVED, "결과", None, None, None),
        ("Q", "열부하", "Q", "W", Role.DERIVED, "결과", None, None, None),
    ])


def thermo_registry(v: dict) -> ParameterRegistry:
    return _reg([
        ("dH", "엔탈피변화", "dH", "kJ/mol", Role.INPUT, "엔탈피", v["dH"], -2000, 2000),
        ("dS", "엔트로피변화", "dS", "J/mol/K", Role.INPUT, "엔트로피", v["dS"], -2000, 2000),
        ("temperature", "반응온도", "T", "degC", Role.INPUT, "온도", v["T"], -273.15, None),
        ("R", "기체상수", "R", "J/mol", Role.CONSTANT, "상수", 8.314462618, None, None),
        ("dG", "자유에너지", "dG", "J/mol", Role.DERIVED, "결과", None, None, None),
        ("K_eq", "평형상수", "K_eq", "-", Role.DERIVED, "결과", None, None, None),
    ])


# --- 스트림릿 UI (Google 스타일 테마는 .streamlit/config.toml) --------------

def main() -> None:
    st.set_page_config(page_title="Reactor Platform Console", page_icon="🧪", layout="wide")
    st.title("Chemical Reactor Parameter Optimization Platform")
    st.caption("Parameter-driven · Self-documenting · Validate-before-compute")

    with st.sidebar:
        st.header("Input parameters")
        A = st.number_input("빈도인자 A [1/s]", value=1_000_000.0, format="%.1f")
        Ea = st.number_input("활성화 에너지 Ea [kJ/mol]", value=50.0)
        T = st.slider("반응 온도 T [°C]", -50.0, 250.0, 80.0)
        n = st.number_input("반응 차수 n [-]", value=1.0, min_value=0.0, max_value=3.0, step=1.0)
        C_A0 = st.number_input("초기 농도 C_A0 [mol/L]", value=2.0, min_value=0.0)
        v0 = st.number_input("부피 유량 v0 [L/min]", value=10.0, min_value=0.0)
        V = st.number_input("반응기 부피 V [L]", value=100.0, min_value=0.0)
        st.divider()
        st.subheader("Energy (M3)")
        dH_rxn = st.number_input("반응열 ΔH_rxn [kJ/mol]", value=-80.0)
        cp_flow = st.number_input("공급 열용량 유량 cp_flow [W/K]", value=500.0, min_value=0.0)
        T_feed = st.slider("공급 온도 T_feed [°C]", -50.0, 250.0, 25.0)
        st.divider()
        st.subheader("Thermo (M2)")
        dH = st.number_input("반응 엔탈피 ΔH [kJ/mol]", value=-50.0)
        dS = st.number_input("반응 엔트로피 ΔS [J/mol/K]", value=80.0)

    vals = dict(A=A, Ea=Ea, T=T, n=n, C_A0=C_A0, v0=v0, V=V,
                dH_rxn=dH_rxn, cp_flow=cp_flow, T_feed=T_feed, dH=dH, dS=dS)

    try:
        reg = cstr_energy_registry(vals)
        cstr_res = CSTR(reg).solve()
        energy_res = EnergyBalance(cstr_energy_registry(vals)).solve()
        thermo_res = ThermoAnalyzer(thermo_registry(vals)).solve()
    except Exception as exc:  # noqa: BLE001
        st.error(f"입력 검증 실패: {exc}")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conversion X", f"{cstr_res.values['X']:.3f}")
    c2.metric("Rate const k [/s]", f"{cstr_res.values['k']:.4g}")
    duty = energy_res.duty
    c3.metric(f"Heat duty Q [kW] · {duty}", f"{energy_res.values['Q'] / 1000:.2f}")
    c4.metric("Thermo", thermo_res.verdict, f"ΔG={thermo_res.values['dG']:.0f} J/mol")

    st.subheader("Explainable report")
    tab1, tab2, tab3 = st.tabs(["CSTR", "Energy (M3)", "Thermo (M2)"])
    with tab1:
        st.code(CSTR(cstr_energy_registry(vals)).report(cstr_res), language="text")
    with tab2:
        st.code(EnergyBalance(cstr_energy_registry(vals)).report(energy_res), language="text")
    with tab3:
        st.code(ThermoAnalyzer(thermo_registry(vals)).report(thermo_res), language="text")

    st.subheader("Scenario & Sensitivity Lab")
    lo, hi, step = 40.0, 120.0, 20.0
    temps = [lo + i * step for i in range(int((hi - lo) / step) + 1)]
    econ = Economics(product_price=5.0, feed_price=1.0, fixed_opex=1000.0, operating_hours=8000.0)

    rows = []
    chart = {}
    for tv in temps:
        vv = dict(vals)
        vv["T"] = tv
        r = cstr_energy_registry(vv)
        res = CSTR(r).solve()
        e = EnergyBalance(cstr_energy_registry(vv)).solve()
        prod = r.si("v0") * r.si("C_A0") * res.values["X"]
        seconds = econ.operating_hours * 3600.0
        revenue = prod * seconds * econ.product_price
        feed_cost = (r.si("v0") * r.si("C_A0")) * seconds * econ.feed_price
        profit = revenue - feed_cost - econ.fixed_opex
        rows.append({"T [°C]": tv, "X": round(res.values["X"], 4),
                     "k [/s]": round(res.values["k"], 5),
                     "Q [kW]": round(e.values["Q"] / 1000, 2),
                     "profit [$]": round(profit)})
        chart[tv] = res.values["X"]

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.line_chart(pd.DataFrame({"X": chart}))


if __name__ == "__main__":
    main()
