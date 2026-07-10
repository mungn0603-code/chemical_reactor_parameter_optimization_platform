"""eda/report.py — EDA 보고서 자동 생성(Markdown / HTML).

프로파일·발견사항·선택한 그래프·전처리 이력·추천을 하나의 보고서로 요약한다.
HTML 은 순수 문자열로 생성하므로 외부 의존성이 없다(선택적으로 plotly 그래프를
div 로 삽입할 수 있다).
"""
from __future__ import annotations

import html
from datetime import datetime
from typing import Optional


from .history import HistoryManager
from .profile import DataProfile
from .recommendation import (
    recommend_analyses,
    top_recommendation_text,
)


def build_report_markdown(
    profile: DataProfile,
    history: Optional[HistoryManager] = None,
    selected_charts: Optional[list[str]] = None,
) -> str:
    """EDA 결과를 Markdown 문자열로 만든다."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append("# EDA 분석 보고서")
    lines.append(f"_생성 시각: {now}_\n")

    # 1) 데이터 품질.
    lines.append("## 1. 데이터 품질")
    lines.append(f"- 행 수: **{profile.n_rows}**, 열 수: **{profile.n_cols}**")
    lines.append(
        f"- 수치형 {len(profile.numeric_cols)} · 범주형 {len(profile.categorical_cols)} "
        f"· 날짜형 {len(profile.datetime_cols)}")
    lines.append(f"- 데이터 품질 점수: **{profile.quality_score:.1f} / 100**")
    lines.append(f"- 결측치 총 {profile.total_missing}개 · 중복행 {profile.n_duplicates}개\n")

    # 2) 기초 통계.
    lines.append("## 2. 기초 통계 (수치형)")
    lines.append("| 변수 | 평균 | 표준편차 | 최소 | 최대 | 왜도 | 첨도 | 이상치 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for c in profile.columns:
        if c.kind != "numeric":
            continue
        lines.append(
            f"| {c.name} | {_fmt(c.mean)} | {_fmt(c.std)} | {_fmt(c.min)} | "
            f"{_fmt(c.max)} | {_fmt(c.skew)} | {_fmt(c.kurtosis)} | {c.n_outliers} |")
    lines.append("")

    # 3) 주요 발견 사항.
    lines.append("## 3. 주요 발견 사항")
    for f in profile.findings:
        lines.append(f"- {f}")
    lines.append("")

    # 4) 상관관계.
    if profile.strong_pairs:
        lines.append("## 4. 상관관계 (강한 쌍)")
        for a, b, r in profile.strong_pairs:
            lines.append(f"- {a} ↔ {b}: r = {r:.2f}")
        lines.append("")

    # 5) 선택한 그래프.
    if selected_charts:
        lines.append("## 5. 생성한 시각화")
        for ch in selected_charts:
            lines.append(f"- {ch}")
        lines.append("")

    # 6) 전처리 내역.
    if history is not None:
        lines.append("## 6. 전처리 내역 (History)")
        lines.append("| step | 시간 | 변경 내용 | 사용자 | 행 | 열 |")
        lines.append("|---|---|---|---|---|---|")
        for rec in history.records():
            lines.append(
                f"| {rec.step} | {rec.timestamp} | {rec.description} | "
                f"{rec.user} | {rec.n_rows} | {rec.n_cols} |")
        lines.append("")

    # 7) 추천 사항.
    lines.append("## 7. 추천 사항")
    lines.append(f"- {top_recommendation_text(profile)}")
    for arec in recommend_analyses(profile)[:5]:
        lines.append(f"- **{arec.label}**: {arec.reason}")
    lines.append("")

    return "\n".join(lines)


def build_report_html(
    profile: DataProfile,
    history: Optional[HistoryManager] = None,
    selected_charts: Optional[list[str]] = None,
    figures_html: Optional[list[str]] = None,
) -> str:
    """EDA 결과를 자체 완결형 HTML 문서로 만든다.

    figures_html 로 plotly figure 의 to_html(full_html=False) 조각을 넘기면
    그래프까지 포함된 보고서가 만들어진다.
    """
    md = build_report_markdown(profile, history, selected_charts)
    body = _markdown_to_html(md)
    figs = ""
    if figures_html:
        figs = "<h2>시각화</h2>" + "\n".join(figures_html)

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>EDA 분석 보고서</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
         max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #202124;
         line-height: 1.6; }}
  h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: .3rem; }}
  h2 {{ color: #174ea6; margin-top: 1.8rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .9rem; }}
  th, td {{ border: 1px solid #dadce0; padding: 6px 10px; text-align: left; }}
  th {{ background: #e8f0fe; }}
  code {{ background: #f1f3f4; padding: 1px 4px; border-radius: 3px; }}
  em {{ color: #5f6368; }}
</style></head>
<body>
{body}
{figs}
</body></html>"""


def _fmt(x: Optional[float]) -> str:
    """숫자를 짧게 포맷(None → '-')."""
    if x is None:
        return "-"
    return f"{x:.4g}"


def _markdown_to_html(md: str) -> str:
    """의존성 없는 최소 Markdown → HTML 변환(제목·표·목록·강조)."""
    out: list[str] = []
    in_table = False
    for raw in md.splitlines():
        line = raw.rstrip()
        # 표 처리.
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue  # 구분선 스킵.
            if not in_table:
                out.append("<table>")
                in_table = True
                tag = "th"
            else:
                tag = "td"
            row = "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False

        if line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("- "):
            out.append(f"<li>{_inline(line[2:])}</li>")
        elif line.startswith("_") and line.endswith("_"):
            out.append(f"<p><em>{html.escape(line.strip('_'))}</em></p>")
        elif line == "":
            out.append("")
        else:
            out.append(f"<p>{_inline(line)}</p>")
    if in_table:
        out.append("</table>")
    return "\n".join(out)


def _inline(text: str) -> str:
    """인라인 강조(**bold**)와 이스케이프."""
    escaped = html.escape(text)
    # 매우 단순한 **bold** 처리.
    parts = escaped.split("**")
    if len(parts) >= 3:
        rebuilt = ""
        for i, p in enumerate(parts):
            rebuilt += f"<strong>{p}</strong>" if i % 2 == 1 else p
        return rebuilt
    return escaped
