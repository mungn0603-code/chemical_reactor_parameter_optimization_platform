"""test_explain.py — 자기설명 규약이 지켜지는지 검사."""
from pathlib import Path

from reactor_platform.parameters.registry import ParameterRegistry
from reactor_platform.core.reactors.cstr import CSTR

CATALOG = Path(__file__).resolve().parents[1] / "parameters" / "catalog" / "cstr_example.yaml"


def test_all_catalog_params_have_description():
    reg = ParameterRegistry()
    reg.from_yaml(CATALOG)
    for p in reg.all():
        assert p.description and p.description.strip(), f"{p.key} 설명 누락"


def test_reactor_explain_has_speccard_and_inputs():
    reg = ParameterRegistry()
    reg.from_yaml(CATALOG)
    text = CSTR(reg).explain()
    assert "설명 카드" in text
    assert "활성화 에너지" in text


def test_demo_catalog_solves_and_passes_selfcheck():
    reg = ParameterRegistry()
    reg.from_yaml(CATALOG)
    res = CSTR(reg).solve()
    assert res.ok is True
    assert 0.0 <= res.values["X"] <= 1.0
