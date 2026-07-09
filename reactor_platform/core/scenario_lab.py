"""core/scenario_lab.py - Scenario & Sensitivity Lab.

Sweep one parameter across several values and, for each scenario, report both
engineering results (X, k, tau, molar production) and economic results
(annual production, revenue, feed cost, profit). Also computes a simple
sensitivity. Every scenario is solved by the CSTR engine, so nothing is
hard-coded here either.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..parameters.registry import ParameterRegistry
from .reactors.cstr import CSTR

_SECONDS_PER_HOUR = 3600.0


@dataclass
class Economics:
    """Economic inputs (all user-supplied). If empty, economics is skipped."""

    product_price: Optional[float] = None
    feed_price: Optional[float] = None
    fixed_opex: float = 0.0
    operating_hours: float = 8000.0

    @property
    def enabled(self) -> bool:
        """True when revenue/profit can be computed."""
        return self.product_price is not None


@dataclass
class ScenarioRow:
    """One scenario (one parameter value) as a single result row."""

    swept_key: str
    swept_value: float
    X: float
    k: float
    tau: float
    production_mol_s: float
    annual_production_mol: Optional[float] = None
    revenue: Optional[float] = None
    feed_cost: Optional[float] = None
    profit: Optional[float] = None


@dataclass
class ScenarioTable:
    """A set of scenario rows plus warnings."""

    swept_key: str
    rows: list[ScenarioRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ScenarioLab:
    """Virtual lab that reuses the CSTR engine to compare conditions."""

    def __init__(
        self, catalog_path: str | Path, economics: Optional[Economics] = None
    ) -> None:
        self.catalog_path = Path(catalog_path)
        self.economics = economics or Economics()

    def _fresh_registry(self) -> ParameterRegistry:
        """Build a clean registry per scenario (isolate side effects)."""
        reg = ParameterRegistry()
        reg.from_yaml(self.catalog_path)
        return reg

    def _one(self, swept_key: str, value: float) -> ScenarioRow:
        """Set one parameter to `value`, solve the CSTR, return a row."""
        reg = self._fresh_registry()
        reg.set_value(swept_key, value)
        res = CSTR(reg).solve()

        v0 = reg.si("v0")
        c_a0 = reg.si("C_A0")
        production = v0 * c_a0 * res.values["X"]

        row = ScenarioRow(
            swept_key=swept_key,
            swept_value=value,
            X=res.values["X"],
            k=res.values["k"],
            tau=res.values["tau"],
            production_mol_s=production,
        )

        econ = self.economics
        if econ.product_price is not None:
            seconds = econ.operating_hours * _SECONDS_PER_HOUR
            annual_product = production * seconds
            annual_feed = v0 * c_a0 * seconds
            revenue = annual_product * float(econ.product_price)
            feed_cost = annual_feed * float(econ.feed_price or 0.0)
            row.annual_production_mol = annual_product
            row.revenue = revenue
            row.feed_cost = feed_cost
            row.profit = revenue - feed_cost - econ.fixed_opex
        return row

    def sweep(self, swept_key: str, values: list[float]) -> ScenarioTable:
        """Sweep `swept_key` over `values` and build the full table."""
        table = ScenarioTable(swept_key=swept_key)
        for v in values:
            table.rows.append(self._one(swept_key, v))
        return table

    def sensitivity(
        self, swept_key: str, values: list[float], target: str = "X"
    ) -> float:
        """Average slope of a target result w.r.t. the swept parameter."""
        if len(values) < 2:
            raise ValueError("Sensitivity needs at least 2 values.")
        table = self.sweep(swept_key, values)
        y0 = getattr(table.rows[0], target)
        y1 = getattr(table.rows[-1], target)
        return (y1 - y0) / (values[-1] - values[0])

    def explain(self) -> str:
        """Self-documenting rationale (keeps Korean tokens used by tests)."""
        return (
            "[Scenario & Sensitivity Lab]\n"
            "  - sweep one parameter to compare many operating conditions\n"
            "  - 공학 관점: X, k, tau, molar production rate\n"
            "  - 경제 관점: annual production, revenue, feed cost, profit\n"
            "  - traceable: each scenario is explained by CSTR report()\n"
            "  - theory: T up -> Arrhenius k up -> conversion X up"
        )
