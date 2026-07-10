"""test_eda_recommendation.py — 규칙 기반 추천 엔진 검증."""
import pandas as pd

from reactor_platform.eda.profile import profile_dataframe
from reactor_platform.eda.recommendation import (
    recommend_analyses,
    recommend_visualizations,
    top_recommendation_text,
)
from reactor_platform.eda.sample import make_sample_dataset


def test_every_analysis_has_reason():
    p = profile_dataframe(make_sample_dataset())
    recs = recommend_analyses(p)
    assert recs
    assert all(r.reason.strip() for r in recs)


def test_recommendations_sorted_by_score():
    p = profile_dataframe(make_sample_dataset())
    scores = [r.score for r in recommend_analyses(p)]
    assert scores == sorted(scores, reverse=True)


def test_domain_temperature_conversion_recommended():
    p = profile_dataframe(make_sample_dataset())
    keys = {r.key for r in recommend_analyses(p)}
    assert "temp_effect" in keys  # Temperature + Conversion 열이 있으므로


def test_categorical_only_recommends_count_plot():
    df = pd.DataFrame({"cat": ["a", "b", "a", "c", "b"] * 4})
    p = profile_dataframe(df)
    kinds = {v.kind for v in recommend_visualizations(p)}
    assert "count" in kinds
    assert "Count Plot" in top_recommendation_text(p)


def test_strong_correlation_boosts_scatter():
    df = pd.DataFrame({"x": range(30), "y": [2 * i for i in range(30)]})
    p = profile_dataframe(df)
    vizzes = recommend_visualizations(p)
    top = vizzes[0]
    assert top.kind == "scatter"


def test_every_viz_has_reason_and_columns():
    p = profile_dataframe(make_sample_dataset())
    for v in recommend_visualizations(p):
        assert v.reason.strip()
        assert isinstance(v.columns, list)
