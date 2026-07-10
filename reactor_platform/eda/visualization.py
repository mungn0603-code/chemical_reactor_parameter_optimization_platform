"""eda/visualization.py — 추천 시각화 생성(plotly).

recommendation 이 고른 kind 를 실제 그래프로 만든다. 모든 그래프는 plotly Figure
로 반환되어 Streamlit(st.plotly_chart)이나 HTML 리포트에서 그대로 쓸 수 있다.

plotly 가 없으면 명확한 오류를 던진다(선택 의존성).
"""
from __future__ import annotations

from typing import Any, Optional

import pandas as pd

SUPPORTED_KINDS = [
    "histogram", "scatter", "correlation_heatmap", "pair_plot", "box",
    "violin", "line", "surface_3d", "contour", "parallel", "radar", "count",
]


def _require_plotly() -> Any:
    """plotly.express 를 지연 임포트한다(선택 의존성)."""
    try:
        import plotly.express as px  # noqa: F401
        import plotly.graph_objects as go  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "시각화에는 plotly 가 필요합니다. `pip install plotly` 후 다시 시도하세요."
        ) from exc
    return px, go


def build_figure(
    kind: str,
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    x: Optional[str] = None,
    y: Optional[str] = None,
    z: Optional[str] = None,
    color: Optional[str] = None,
) -> Any:
    """kind 에 맞는 plotly Figure 를 만든다.

    columns 로 관련 열을 넘기거나, x/y/z/color 로 직접 지정할 수 있다.
    """
    px, go = _require_plotly()
    cols = columns or []

    def pick(idx: int, fallback: Optional[str]) -> Optional[str]:
        if fallback is not None:
            return fallback
        return cols[idx] if len(cols) > idx else None

    if kind == "histogram":
        col = pick(0, x)
        return px.histogram(df, x=col, marginal="box", title=f"Histogram · {col}")

    if kind == "scatter":
        xc, yc = pick(0, x), pick(1, y)
        return px.scatter(df, x=xc, y=yc, color=color, trendline=None,
                          title=f"Scatter · {xc} vs {yc}")

    if kind == "correlation_heatmap":
        use = cols or list(df.select_dtypes(include="number").columns)
        corr = df[use].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=".2f", aspect="auto",
                        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                        title="Correlation Heatmap")
        return fig

    if kind == "pair_plot":
        use = cols or list(df.select_dtypes(include="number").columns)
        use = use[:6]
        return px.scatter_matrix(df, dimensions=use, color=color, title="Pair Plot")

    if kind == "box":
        use = cols or list(df.select_dtypes(include="number").columns)
        melted = df[use].melt(var_name="변수", value_name="값")
        return px.box(melted, x="변수", y="값", title="Box Plot")

    if kind == "violin":
        xc, yc = pick(0, x), pick(1, y)
        return px.violin(df, x=xc, y=yc, box=True, points="outliers",
                         title=f"Violin · {yc} by {xc}")

    if kind == "line":
        xc, yc = pick(0, x), pick(1, y)
        return px.line(df.sort_values(xc), x=xc, y=yc, title=f"Line · {yc} over {xc}")

    if kind == "surface_3d":
        xc, yc, zc = pick(0, x), pick(1, y), pick(2, z)
        if xc is None or yc is None or zc is None:
            raise ValueError("3D Surface 에는 x·y·z 3개 열이 필요합니다.")
        return _surface(go, df, xc, yc, zc)

    if kind == "contour":
        xc, yc, zc = pick(0, x), pick(1, y), pick(2, z)
        fig = go.Figure(data=go.Contour(
            x=df[xc], y=df[yc], z=df[zc], colorscale="Viridis",
            contours=dict(showlabels=True)))
        fig.update_layout(title=f"Contour · {zc}", xaxis_title=xc, yaxis_title=yc)
        return fig

    if kind == "parallel":
        use = cols or list(df.select_dtypes(include="number").columns)
        return px.parallel_coordinates(df, dimensions=use, title="Parallel Coordinates")

    if kind == "radar":
        return _radar(go, df, cols, color)

    if kind == "count":
        col = pick(0, x)
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, "count"]
        return px.bar(counts, x=col, y="count", title=f"Count · {col}")

    raise ValueError(f"지원하지 않는 그래프 종류: {kind!r} (지원: {SUPPORTED_KINDS})")


def _surface(go: Any, df: pd.DataFrame, x: str, y: str, z: str) -> Any:
    """산점 데이터를 격자로 피벗해 3D 표면을 만든다."""
    grid = df.pivot_table(index=y, columns=x, values=z, aggfunc="mean")
    fig = go.Figure(data=[go.Surface(
        x=grid.columns.values, y=grid.index.values, z=grid.values,
        colorscale="Viridis")])
    fig.update_layout(
        title=f"3D Surface · {z}",
        scene=dict(xaxis_title=x, yaxis_title=y, zaxis_title=z))
    return fig


def _radar(go: Any, df: pd.DataFrame, cols: list[str], color: Optional[str]) -> Any:
    """범주(group)별 지표 평균을 방사형으로 비교한다."""
    if not cols:
        raise ValueError("radar 차트에는 (그룹열 + 지표열들) 이 필요합니다.")
    group = color or cols[0]
    metrics = [c for c in cols[1:] if c in df.columns]
    if not metrics:
        metrics = list(df.select_dtypes(include="number").columns)[:5]
    agg = df.groupby(group)[metrics].mean()
    # 지표 스케일을 0~1 로 정규화해 비교 가능하게 만든다.
    norm = (agg - agg.min()) / (agg.max() - agg.min()).replace(0, 1)
    fig = go.Figure()
    for name, row in norm.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=list(row.values) + [row.values[0]],
            theta=metrics + [metrics[0]],
            fill="toself", name=str(name)))
    fig.update_layout(title="Radar Chart (정규화)", polar=dict(radialaxis=dict(range=[0, 1])))
    return fig
