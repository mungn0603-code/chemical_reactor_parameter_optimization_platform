"""reactor_platform.webui — 통합 대시보드 UI 계층(streamlit).

한 브라우저 안에서 카드 클릭으로 세 기능 사이를 이동한다.
  - reactor_view : M1→M2→M3 순차 반응기 계산(반응식 입력 → 열역학 자동 설정)
  - eda(.ui)     : AI 기반 EDA Assistant
  - report_view  : 통합 보고서

계산 엔진(core/*, parameters/*)과 EDA 로직(eda/*)은 전혀 변경하지 않고 조합만 한다.
이 패키지는 streamlit 이 설치된 경우에만 임포트된다.
"""
