"""core/reactions.py — 반응식 → 화학종 매핑 → 표준 반응 열역학 자동 계산.

교과서 이론(표준상태 298.15 K)
------------------------------
표준 생성엔탈피 ΔHf°, 표준 몰엔트로피 S° 로부터 Hess 의 법칙으로 반응의
표준 열역학량을 계산한다(Smith·Van Ness·Abbott, *Introduction to Chemical
Engineering Thermodynamics*; Fogler, *Elements of CRE* 부록 참조).

    ΔH_rxn° = Σ ν_i · ΔHf°_i      (생성물 ν>0, 반응물 ν<0)      [Hess 의 법칙]
    ΔS_rxn° = Σ ν_i · S°_i
    ΔG_rxn° = ΔH_rxn° − T · ΔS_rxn°   (ΔH°, ΔS° 는 298.15 K 값으로 근사)
    K_eq    = exp(−ΔG_rxn° / (R·T))

이 값들은 기존 ThermoAnalyzer(dH, dS)·EnergyBalance(dH_rxn) 에 그대로 주입되어
계산 로직을 전혀 바꾸지 않고 '반응식 입력 → 자동 설정' 을 가능하게 한다.

데이터 출처: NIST Chemistry WebBook / CRC Handbook / Smith·Van Ness·Abbott 부록 C
의 널리 통용되는 표준값(298.15 K). 값은 species DB 에 명시되어 추적 가능하다.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

R_GAS: float = 8.314462618  # J/(mol·K)
T_STD: float = 298.15       # K, 표준상태 온도


def _safe_exp(x: float) -> float:
    """math.exp 의 오버플로/언더플로를 막는다(K_eq 가 float 범위를 넘는 경우)."""
    if x > 700.0:
        return math.inf
    if x < -700.0:
        return 0.0
    return math.exp(x)


# --------------------------------------------------------------------------- #
# 화학종 열화학 데이터베이스 (298.15 K 표준값)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Species:
    """하나의 화학종에 대한 표준 열화학 데이터.

    key   : 사용자가 반응식에 쓰는 표기(상태 포함, 예: 'H2O(l)').
    formula: 원소 조성 문자열(상태 제외, 예: 'H2O') — 원소 균형 검사에 사용.
    dHf298 : 표준 생성엔탈피 [kJ/mol]  (원소 표준상태 = 0).
    S298   : 표준 몰엔트로피 [J/(mol·K)].
    name   : 한글/일반 명칭.
    phase  : 상태(g/l/s/aq).
    """

    key: str
    formula: str
    dHf298: float
    S298: float
    name: str
    phase: str = "g"


def _s(key, formula, dHf, S, name, phase="g") -> tuple[str, Species]:
    return key, Species(key, formula, dHf, S, name, phase)


# 대표적인 반응공학 교과서 화학종(298.15 K). 값 단위: ΔHf°[kJ/mol], S°[J/mol/K].
SPECIES_DB: dict[str, Species] = dict([
    # 원소 표준상태(ΔHf°=0).
    _s("N2", "N2", 0.0, 191.6, "질소", "g"),
    _s("H2", "H2", 0.0, 130.7, "수소", "g"),
    _s("O2", "O2", 0.0, 205.2, "산소", "g"),
    _s("Cl2", "Cl2", 0.0, 223.1, "염소", "g"),
    _s("C(graphite)", "C", 0.0, 5.7, "흑연 탄소", "s"),
    _s("S(s)", "S", 0.0, 32.1, "황(사방정)", "s"),
    # 무기 화합물.
    _s("NH3", "NH3", -45.9, 192.8, "암모니아", "g"),
    _s("H2O(g)", "H2O", -241.8, 188.8, "물(기체)", "g"),
    _s("H2O(l)", "H2O", -285.8, 70.0, "물(액체)", "l"),
    _s("CO", "CO", -110.5, 197.7, "일산화탄소", "g"),
    _s("CO2", "CO2", -393.5, 213.8, "이산화탄소", "g"),
    _s("NO", "NO", 91.3, 210.8, "일산화질소", "g"),
    _s("NO2", "NO2", 33.2, 240.1, "이산화질소", "g"),
    _s("SO2", "SO2", -296.8, 248.2, "이산화황", "g"),
    _s("SO3", "SO3", -395.7, 256.8, "삼산화황", "g"),
    _s("HCl", "HCl", -92.3, 186.9, "염화수소", "g"),
    _s("H2O2(l)", "H2O2", -187.8, 109.6, "과산화수소", "l"),
    # 탄화수소·함산소 유기물.
    _s("CH4", "CH4", -74.6, 186.3, "메탄", "g"),
    _s("C2H2", "C2H2", 227.4, 200.9, "아세틸렌", "g"),
    _s("C2H4", "C2H4", 52.4, 219.3, "에틸렌", "g"),
    _s("C2H6", "C2H6", -84.0, 229.2, "에탄", "g"),
    _s("C3H8", "C3H8", -104.7, 270.3, "프로판", "g"),
    _s("C4H10", "C4H10", -125.6, 310.2, "부탄", "g"),
    _s("CH3OH(l)", "CH4O", -238.4, 126.8, "메탄올(액체)", "l"),
    _s("CH3OH(g)", "CH4O", -201.0, 239.9, "메탄올(기체)", "g"),
    _s("C2H5OH(l)", "C2H6O", -277.6, 160.7, "에탄올(액체)", "l"),
    _s("C2H5OH(g)", "C2H6O", -234.8, 281.6, "에탄올(기체)", "g"),
    _s("CH3COOH(l)", "C2H4O2", -484.5, 159.8, "아세트산(액체)", "l"),
    _s("C6H6(l)", "C6H6", 49.0, 173.4, "벤젠(액체)", "l"),
    _s("C6H12O6(s)", "C6H12O6", -1273.3, 212.1, "포도당", "s"),
])


# --------------------------------------------------------------------------- #
# 반응식 파싱 · 원소 균형
# --------------------------------------------------------------------------- #
_ARROW = re.compile(r"->|=>|=|→|⇌|⟶")
_TERM = re.compile(r"^\s*(\d*\.?\d*)\s*(.+?)\s*$")
_ELEMENT = re.compile(r"([A-Z][a-z]?)(\d*)")


class ReactionError(ValueError):
    """반응식 파싱/매핑 오류(미등록 화학종, 화살표 없음, 불균형 등)."""


def parse_formula(formula: str) -> dict[str, int]:
    """화학식을 원소 개수 dict 로 파싱한다(괄호 미지원, 단순 조성식).

    예: 'C2H5OH' 로 쓰지 말고 조성식 'C2H6O' 를 쓴다(Species.formula 규칙).
    """
    counts: dict[str, int] = {}
    for elem, num in _ELEMENT.findall(formula):
        if not elem:
            continue
        counts[elem] = counts.get(elem, 0) + (int(num) if num else 1)
    return counts


def _lookup(token: str) -> Species:
    """반응식 토큰을 Species 로 매핑한다. 상태 미지정 시 기체를 시도."""
    token = token.strip()
    if token in SPECIES_DB:
        return SPECIES_DB[token]
    # 상태를 안 붙인 경우 기체판을 우선 시도(예: 'H2O' → 'H2O(g)').
    if f"{token}(g)" in SPECIES_DB:
        return SPECIES_DB[f"{token}(g)"]
    raise ReactionError(
        f"등록되지 않은 화학종: '{token}'. SPECIES_DB 에 추가하거나 표기를 확인하세요."
    )


@dataclass
class Reaction:
    """파싱된 반응. 계수는 반응물 음수, 생성물 양수로 통일한다."""

    reactants: list[tuple[float, Species]]  # (계수>0, 화학종)
    products: list[tuple[float, Species]]
    raw: str

    def stoich(self) -> list[tuple[float, Species]]:
        """부호 있는 계수 목록(ν<0 반응물, ν>0 생성물)."""
        return [(-c, s) for c, s in self.reactants] + [(c, s) for c, s in self.products]

    def equation(self) -> str:
        """사람이 읽는 균형 반응식 문자열."""
        def side(terms):
            return " + ".join(
                (f"{c:g} {s.key}" if abs(c - 1.0) > 1e-9 else s.key)
                for c, s in terms)
        return f"{side(self.reactants)} → {side(self.products)}"


def parse_reaction(text: str) -> Reaction:
    """'N2 + 3 H2 -> 2 NH3' 같은 문자열을 Reaction 으로 파싱한다."""
    if not _ARROW.search(text):
        raise ReactionError("반응식에 화살표(-> 또는 =)가 없습니다. 예: 'N2 + 3 H2 -> 2 NH3'")
    lhs, rhs = _ARROW.split(text, maxsplit=1)

    def parse_side(side: str) -> list[tuple[float, Species]]:
        terms: list[tuple[float, Species]] = []
        for part in side.split("+"):
            part = part.strip()
            if not part:
                continue
            m = _TERM.match(part)
            if not m:
                raise ReactionError(f"항을 해석할 수 없습니다: '{part}'")
            coeff_str, token = m.group(1), m.group(2)
            coeff = float(coeff_str) if coeff_str else 1.0
            terms.append((coeff, _lookup(token)))
        return terms

    reactants = parse_side(lhs)
    products = parse_side(rhs)
    if not reactants or not products:
        raise ReactionError("반응물 또는 생성물이 비어 있습니다.")
    return Reaction(reactants=reactants, products=products, raw=text.strip())


def element_balance(rxn: Reaction) -> tuple[bool, dict[str, float]]:
    """원소 균형을 검사한다. (균형 여부, 원소별 (생성물−반응물) 잔차)."""
    diff: dict[str, float] = {}
    for coeff, sp in rxn.stoich():  # coeff 부호 포함
        for elem, num in parse_formula(sp.formula).items():
            diff[elem] = diff.get(elem, 0.0) + coeff * num
    balanced = all(abs(v) < 1e-9 for v in diff.values())
    residual = {e: v for e, v in diff.items() if abs(v) > 1e-9}
    return balanced, residual


# --------------------------------------------------------------------------- #
# 표준 반응 열역학 (Hess 의 법칙)
# --------------------------------------------------------------------------- #
@dataclass
class ReactionThermo:
    """반응식으로부터 자동 계산된 표준 반응 열역학량."""

    reaction: Reaction
    dH_rxn: float      # 표준 반응 엔탈피 [kJ/mol]
    dS_rxn: float      # 표준 반응 엔트로피 [J/mol/K]
    dG_rxn: float      # 표준 반응 깁스에너지 [kJ/mol] (온도 T)
    K_eq: float        # 평형상수 (온도 T)
    T: float           # 계산에 쓴 온도 [K]
    balanced: bool
    residual: dict[str, float] = field(default_factory=dict)
    steps: list[str] = field(default_factory=list)

    @property
    def enthalpy_label(self) -> str:
        """발열/흡열 판정(교과서 정의)."""
        if self.dH_rxn < 0:
            return "발열(exothermic)"
        if self.dH_rxn > 0:
            return "흡열(endothermic)"
        return "열중립"

    @property
    def spontaneity_label(self) -> str:
        """ΔG 부호로 자발성 판정."""
        if self.dG_rxn < 0:
            return "자발적"
        if self.dG_rxn > 0:
            return "비자발적"
        return "평형"


def reaction_thermochemistry(rxn: Reaction, T: float = T_STD) -> ReactionThermo:
    """Hess 의 법칙으로 ΔH_rxn°, ΔS_rxn°, ΔG_rxn°, K_eq 를 계산한다.

    ΔH°, ΔS° 는 298.15 K 표준값을 사용하고, ΔG(T)=ΔH°−T·ΔS° 로 온도만 반영한다
    (표준상태 근사 — 교과서 기본형). T 는 절대온도[K].
    """
    if T <= 0:
        raise ReactionError("절대온도 T 는 0 K 보다 커야 합니다.")

    balanced, residual = element_balance(rxn)

    steps: list[str] = []
    # ΔH_rxn° = Σ ν·ΔHf°
    h_terms = []
    dH = 0.0
    for coeff, sp in rxn.stoich():
        dH += coeff * sp.dHf298
        h_terms.append(f"({coeff:+g})·({sp.dHf298:g})")
    steps.append("ΔH_rxn° = Σν·ΔHf° = " + " + ".join(h_terms) + f" = {dH:.4g} kJ/mol")

    # ΔS_rxn° = Σ ν·S°
    s_terms = []
    dS = 0.0
    for coeff, sp in rxn.stoich():
        dS += coeff * sp.S298
        s_terms.append(f"({coeff:+g})·({sp.S298:g})")
    steps.append("ΔS_rxn° = Σν·S° = " + " + ".join(s_terms) + f" = {dS:.4g} J/mol·K")

    # ΔG(T) = ΔH° − T·ΔS°  (ΔH° kJ, ΔS° J → kJ 로 환산)
    dG = dH - T * (dS / 1000.0)
    steps.append(
        f"ΔG_rxn°(T={T:.2f}K) = ΔH° − T·ΔS° = {dH:.4g} − {T:.2f}·({dS:.4g}/1000) "
        f"= {dG:.4g} kJ/mol")

    # K_eq = exp(−ΔG/RT) (ΔG 를 J/mol 로). 지수가 매우 크면 float 범위를 넘으므로 보호.
    exponent = -(dG * 1000.0) / (R_GAS * T)
    K_eq = _safe_exp(exponent)
    steps.append(f"K_eq = exp(−ΔG/RT) = exp({exponent:.4g}) = {K_eq:.4g}")

    return ReactionThermo(
        reaction=rxn, dH_rxn=dH, dS_rxn=dS, dG_rxn=dG, K_eq=K_eq, T=T,
        balanced=balanced, residual=residual, steps=steps)


def analyze_reaction(text: str, T: float = T_STD) -> ReactionThermo:
    """반응식 문자열 하나로 파싱→매핑→열역학 계산을 한 번에 수행한다."""
    return reaction_thermochemistry(parse_reaction(text), T)


# --------------------------------------------------------------------------- #
# 교과서 대표 반응 라이브러리(가이드/드롭다운용)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NamedReaction:
    """이름이 붙은 대표 반응(교육용 프리셋)."""

    name: str
    equation: str
    note: str


REACTION_LIBRARY: list[NamedReaction] = [
    NamedReaction("암모니아 합성 (Haber–Bosch)", "N2 + 3 H2 -> 2 NH3",
                  "발열·몰수 감소 → 저온·고압 유리(르샤틀리에)."),
    NamedReaction("메탄 완전연소", "CH4 + 2 O2 -> CO2 + 2 H2O(g)",
                  "대표적 강발열 반응(연소열)."),
    NamedReaction("수성가스 전환 (WGS)", "CO + H2O(g) -> CO2 + H2",
                  "약발열·몰수 불변 → 온도 영향 완만."),
    NamedReaction("SO2 산화 (접촉법)", "2 SO2 + O2 -> 2 SO3",
                  "황산 제조 핵심 단계, 발열."),
    NamedReaction("에틸렌 수소화", "C2H4 + H2 -> C2H6",
                  "발열 부가반응."),
    NamedReaction("메탄올 합성", "CO + 2 H2 -> CH3OH(g)",
                  "발열·몰수 감소 → 고압 유리."),
    NamedReaction("에탄올 완전연소", "C2H5OH(l) + 3 O2 -> 2 CO2 + 3 H2O(g)",
                  "바이오연료 연소열."),
    NamedReaction("일산화질소 생성", "N2 + O2 -> 2 NO",
                  "강흡열·고온에서만 진행(NOx 생성)."),
    NamedReaction("포도당 완전연소", "C6H12O6(s) + 6 O2 -> 6 CO2 + 6 H2O(l)",
                  "대사·연소의 기준 반응."),
]
