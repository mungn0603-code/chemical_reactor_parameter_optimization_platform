"""test_scenario_lab.py - virtual lab: physical sanity + economics checks."""
from pathlib import Path

import pytest

from reactor_platform.core.scenario_lab import Economics, ScenarioLab

CATALOG = (
    Path(__file__).resolve().parents[1] / "parameters" / "catalog" / "cstr_example.yaml"
)


def test_sweep_returns_a_row_per_value():
    table = ScenarioLab(CATALOG).sweep("temperature", [60.0, 80.0, 100.0])
    assert len(table.rows) == 3
    assert all(0.0 <= r.X <= 1.0 for r in table.rows)


def test_conversion_increases_with_temperature():
    table = ScenarioLab(CATALOG).sweep("temperature", [40.0, 70.0, 100.0])
    xs = [r.X for r in table.rows]
    assert xs[0] < xs[1] < xs[2]


def test_economics_computed_when_enabled():
    econ = Economics(
        product_price=5.0, feed_price=1.0, fixed_opex=1000.0, operating_hours=8000.0
    )
    row = ScenarioLab(CATALOG, economics=econ).sweep("temperature", [80.0]).rows[0]
    assert row.revenue is not None and row.revenue > 0
    assert row.profit == pytest.approx(row.revenue - row.feed_cost - 1000.0)


def test_economics_skipped_when_disabled():
    row = ScenarioLab(CATALOG).sweep("temperature", [80.0]).rows[0]
    assert row.revenue is None and row.profit is None


def test_sensitivity_positive_for_temperature():
    s = ScenarioLab(CATALOG).sensitivity("temperature", [60.0, 100.0], target="X")
    assert s > 0


def test_sensitivity_requires_two_values():
    with pytest.raises(ValueError):
        ScenarioLab(CATALOG).sensitivity("temperature", [80.0])


def test_explain_mentions_both_perspectives():
    text = ScenarioLab(CATALOG).explain()
    assert "공학 관점" in text and "경제 관점" in text
