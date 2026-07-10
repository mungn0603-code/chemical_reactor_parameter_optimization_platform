# 화학 반응기 파라미터 최적화 플랫폼

> AI 기반 화학공학 반응기 최적화 · 경제성 분석 플랫폼.
> **파라미터 주도** · **자기설명** 원칙으로 만든, 검증된 반응기 계산 코어.

[![CI](https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/actions/workflows/ci.yml)
![Coverage](https://raw.githubusercontent.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/python-coverage-comment-action-data/badge.svg)
![python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![ruff](https://img.shields.io/badge/lint-ruff-000000)
![mypy](https://img.shields.io/badge/types-mypy-blue)

## 실행

세 개의 진입 파일이 있다(명명 규칙: `<주제>_app.py`). **통합 대시보드**를 권장한다.

```bash
cd C:\Users\mungn
git clone https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform.git
cd chemical_reactor_parameter_optimization_platform
pip install -r requirements.txt

streamlit run dashboard_app.py          # ⭐ 통합 대시보드 (반응기·EDA·보고서 한 곳에서)
# 또는 개별 앱
streamlit run chemical_reactor_app.py   # 반응기 계산 콘솔(단일 화면)
streamlit run eda_assistant_app.py      # EDA Assistant 단독
```

### 통합 대시보드 (`dashboard_app.py`)

한 브라우저에서 카드/사이드바 클릭으로 세 기능을 오간다.

- **🧪 반응기 계산 (M1→M2→M3 순차)** — 속도론/CSTR → 열역학 → 에너지수지를 순서대로 진행.
  **M2 에서 반응식을 입력**(예: `N2 + 3 H2 -> 2 NH3`)하면 화학종을 열화학 DB 에 매핑해
  **Hess 법칙으로 ΔH_rxn°·ΔS_rxn°·ΔG°·K_eq 를 교과서대로 자동 계산·설정**하고, 이 값이
  M2(열역학)·M3(에너지수지)에 그대로 반영된다. 원소 균형도 자동 검사한다.
- **🔬 EDA Assistant** — 데이터 진단·추천·전처리·시각화·보고서(Undo 가능).
- **📄 통합 보고서** — 반응·열역학·에너지수지 결과를 텍스트·HTML 로 내려받기.

브라우저에서 바로 실행(설치 불필요):

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=mungn0603-code%2Fchemical_reactor_parameter_optimization_platform&branch=main&mainModule=chemical_reactor_app.py)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mungn0603-code/chemical_reactor_parameter_optimization_platform?quickstart=1)

## 왜 이 프로젝트인가

대부분의 반응기 계산기는 상수를 수식 안에 하드코딩한다. 그래서 사용자가 값을 바꿀 수도 없고, 단위·범위 실수를 잡을 방법도 없다. 이 플랫폼은 정반대로 접근한다.

1. **파라미터 주도** — 모든 물리량이 `Parameter` 객체로 관리되며, 수식 어디에도 숫자가 박혀 있지 않다.
2. **자기설명** — 모든 파라미터·수식이 한글 설명을 가지며, `report()`가 입력→공식→중간값→결과→검증을 추적한다.
3. **계산 전 검증** — 6단계 검증이 잘못된 입력을 수식 실행 전에 차단한다.

## 주요 기능

- **Explainable Engineering** — `explain()`/`report()`로 계산 근거를 추적.
- **Scenario & Sensitivity Lab** — 여러 조건을 한 번에 비교(공학 + 경제 관점), 민감도 수치화.
- **열역학 (M2)** — dG, K_eq, 자발성 판정.
- **에너지수지 (M3)** — 열부하 Q, 가열/냉각 판정.
- **반응 열화학 자동 계산** — 반응식 입력 → 화학종 DB 매핑 → Hess 법칙으로 ΔH_rxn°·ΔS_rxn°·ΔG°·K_eq 자동 산출(298.15 K 표준값 기준, 교과서 이론 일치). `reactor_platform/core/reactions.py`.
- **AI 기반 EDA Assistant** — 데이터 품질 진단 → 분석/그래프 추천(이유 포함) → 승인 기반 전처리 → 시각화 → 보고서. 모든 변경은 Undo 가능. (계산 코어와 완전히 분리된 독립 기능)

## AI 기반 EDA Assistant

계산 콘솔과 별개의 진입 파일 `eda_assistant_app.py` 로 실행한다. 계산 엔진(Reactor·Thermo·Kinetics·ParameterRegistry)은 전혀 변경하지 않는다.

```bash
pip install -r requirements.txt        # numpy/scipy/scikit-learn/plotly 포함
streamlit run eda_assistant_app.py
```

워크플로우: **AI 프로파일링 → EDA 추천 → 선택 → 자동 전처리 제안 → 승인 → 시각화 → 보고서 생성**.

- **프로파일링**: 자료형·결측·중복·이상치·상관관계·왜도/첨도·품질 점수를 자동 진단하고 한글로 요약.
- **추천 엔진(규칙 기반)**: 데이터 특성에 맞춰 분석·시각화를 *이유와 함께* 우선순위로 추천. 결정적이며 나중에 LLM 백엔드로 교체 가능.
- **전처리**: 결측(평균/중앙/보간/삭제)·이상치(Winsorizing/제거)·중복 삭제·로그/정규화/표준화·인코딩. 원본 불변, 항상 새 스냅샷.
- **Undo/Redo/History**: 모든 변경을 (적용 시간·내용·사용자·행/열)과 함께 기록.
- **보고서**: Markdown / HTML 자동 생성·다운로드.

모듈은 `reactor_platform/eda/` 에 독립적으로 있으며 streamlit 없이도 임포트·테스트된다.

## 구조

```
dashboard_app.py           ← ⭐ 통합 대시보드 진입 파일
chemical_reactor_app.py    ← 계산 콘솔 진입 파일(단일 화면)
eda_assistant_app.py       ← EDA Assistant 진입 파일(단독)
reactor_platform/          ← 계산 엔진(순수 Python)
  core/                    ← units, kinetics, reactors, thermo, energy, scenario,
                             reactions(반응 열화학), explain
  parameters/              ← schema, registry, validators, catalog/
  eda/                     ← EDA Assistant(profile·recommendation·visualization·
                             preprocessing·outlier·history·report·ui) — 계산 코어와 분리
  webui/                   ← 통합 대시보드 UI(dashboard·reactor_view·report_view) — streamlit 계층
  tests/                   ← pytest
docs/                      ← 설계 문서
```

## 개발 명령

```bash
python -m reactor_platform.demo   # 코어 데모
pytest reactor_platform/tests -v  # 테스트(113)
```

## 품질 & CI

모든 push·PR에서 GitHub Actions가 Ruff · mypy · pytest(3.10/3.11/3.12) · Coverage 배지를 실행한다.

## 로드맵

M0/M1b(CSTR) · Scenario Lab · M2(열역학) · M3(에너지수지) · **반응 열화학 자동 계산** · **AI 기반 EDA Assistant** · **통합 대시보드** 완료. 향후: 온도의존 Cp(T)(Kirchhoff/Shomate), 평형전환율, M4(경제성), M5(최적화), Batch/PFR, AutoML/AI Optimization 연계, Digital Twin.

## 라이선스

MIT
