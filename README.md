# 화학 반응기 파라미터 최적화 플랫폼

> AI 기반 화학공학 반응기 최적화 · 경제성 분석 플랫폼.
> **파라미터 주도** · **자기설명** 원칙으로 만든, 검증된 반응기 계산 코어.

[![CI](https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/actions/workflows/ci.yml)
![Coverage](https://raw.githubusercontent.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/python-coverage-comment-action-data/badge.svg)
![python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![ruff](https://img.shields.io/badge/lint-ruff-000000)
![mypy](https://img.shields.io/badge/types-mypy-blue)

## 실행

이 프로젝트의 진입 파일은 `chemical_reactor_app.py` 이다.
(명명 규칙: 레포별로 `<주제>_app.py` 형태의 고유 이름을 쓴다.)

```bash
pip install -r requirements.txt
streamlit run chemical_reactor_app.py
```

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

## 구조

```
chemical_reactor_app.py    ← 진입 파일(<주제>_app.py)
reactor_platform/          ← 계산 엔진(순수 Python)
  core/                    ← units, kinetics, reactors, thermo, energy, scenario, explain
  parameters/              ← schema, registry, validators, catalog/
  tests/                   ← pytest
docs/                      ← 설계 문서
```

## 개발 명령

```bash
python -m reactor_platform.demo   # 코어 데모
pytest reactor_platform/tests -v  # 테스트(44)
```

## 품질 & CI

모든 push·PR에서 GitHub Actions가 Ruff · mypy · pytest(3.10/3.11/3.12) · Coverage 배지를 실행한다.

## 로드맵

M0/M1b(CSTR) · Scenario Lab · M2(열역학) · M3(에너지수지) 완료. 향후: M4(경제성), M5(최적화), Batch/PFR, AI 추천, Digital Twin.

## 라이선스

MIT
