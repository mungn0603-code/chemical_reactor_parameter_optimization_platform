"""test_eda_report_viz.py — 시각화 생성 + 보고서 출력 검증."""
import pytest

from reactor_platform.eda.history import HistoryManager
from reactor_platform.eda.profile import profile_dataframe
from reactor_platform.eda.report import build_report_html, build_report_markdown
from reactor_platform.eda.sample import make_sample_dataset
from reactor_platform.eda.visualization import build_figure

pytest.importorskip("plotly")


@pytest.mark.parametrize("kind,cols", [
    ("histogram", ["Temperature"]),
    ("scatter", ["Temperature", "Conversion"]),
    ("correlation_heatmap", None),
    ("box", None),
    ("count", ["Catalyst"]),
    ("violin", ["Catalyst", "Conversion"]),
    ("surface_3d", ["Temperature", "Pressure", "Conversion"]),
    ("contour", ["Temperature", "Pressure", "Conversion"]),
    ("parallel", None),
    ("pair_plot", None),
    ("radar", ["Catalyst", "Conversion", "Yield"]),
])
def test_build_each_figure(kind, cols):
    df = make_sample_dataset()
    fig = build_figure(kind, df, columns=cols)
    assert fig is not None
    assert hasattr(fig, "to_dict")


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        build_figure("nope", make_sample_dataset())


def test_markdown_report_has_sections():
    p = profile_dataframe(make_sample_dataset())
    md = build_report_markdown(p)
    for section in ["데이터 품질", "기초 통계", "주요 발견 사항", "추천 사항"]:
        assert section in md


def test_html_report_is_self_contained():
    df = make_sample_dataset()
    h = HistoryManager(df)
    p = profile_dataframe(df)
    html = build_report_html(p, h, ["Histogram"])
    assert html.startswith("<!DOCTYPE html>")
    assert "<table>" in html  # 통계표가 렌더링됨
