# reactor_platform

AI 기반 화학공학 반응기 플랫폼의 코어 패키지.
"파라미터 주도 + 자기설명 + 계산 전 검증" 원칙을 구현한다.

| 개념 | 파일 | 역할 |
|---|---|---|
| Parameter | `parameters/schema.py` | 값+설명+단위+역할+범위 |
| Registry | `parameters/registry.py` | 단일 진실 원천 |
| Validators | `parameters/validators.py` | 6단계 검증 |
| Units | `core/units.py` | SI 경계 변환 |
| Kinetics | `core/kinetics.py` | Arrhenius, 속도식 |
| CSTR | `core/reactors/cstr.py` | 전환율 X |
| Thermo | `core/thermo.py` | dG, K_eq, 자발성 |
| Energy | `core/energy.py` | 열부하 Q |
| Scenario | `core/scenario_lab.py` | 다중 조건 + 경제성 |
| Explain | `core/explain.py` | 설명 카드 |

실행: `python -m reactor_platform.demo` / 테스트: `pytest reactor_platform/tests -v`
