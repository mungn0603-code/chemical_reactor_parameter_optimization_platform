# 로드맵

- **M0/M1b (완료)** — 파라미터 시스템, 6단계 검증, 단위(SI), 반응속도론, 등온 CSTR, 자기설명.
- **Scenario & Sensitivity Lab (완료)** — 다중 조건 비교(공학 + 경제 관점).
- **M2 열역학 (완료)** — dG, K_eq, 자발성 판정.
- **M3 에너지수지 (완료)** — 열부하 Q, 가열/냉각 판정.
- **M4** — 경제성 심화(NPV, IRR, ROI, BEP).
- **M5** — 최적화(SLSQP / Optuna) + 민감도 곡면.
- **M6+** — Batch/PFR, ML 대리모델, FastAPI, Digital Twin.

## 향후 권장 리팩터링(검증 환경 복구 후)

- ParameterRegistry 불변화(외부 변이 차단) + description 강제 테스트 확장.
- core를 kinetics/reactor/thermo/economics 서브패키지로 분리, FormulaEngine 도입.
- ui/ 패널(input/result/graph/report) 분리.
- Scenario와 Economics 역할 분리.
위 항목은 pytest/ruff/mypy 검증과 함께 단계적으로 진행한다.
