"""test_validators.py — 잘못된 입력이 확실히 거부되는지(계산 실수 방지의 핵심)."""
import pytest

from reactor_platform.parameters.registry import ParameterRegistry, RegistryError
from reactor_platform.parameters.schema import Parameter, Role
from reactor_platform.parameters.validators import validate_registry, ValidationError


def _p(key, unit, role, value, mn=None, mx=None):
    return Parameter(key, key, key, unit, role, "테스트용 설명", value=value, min=mn, max=mx)


def test_description_is_mandatory():
    with pytest.raises(ValueError):
        Parameter("x", "x", "x", "-", Role.INPUT, "   ", value=1.0)


def test_missing_value_rejected():
    reg = ParameterRegistry()
    reg.add(_p("temperature", "K", Role.INPUT, None))
    with pytest.raises(ValidationError):
        validate_registry(reg)


def test_unknown_unit_rejected():
    reg = ParameterRegistry()
    reg.add(_p("temperature", "Fahrenheit", Role.INPUT, 300.0))
    with pytest.raises(ValidationError):
        validate_registry(reg)


def test_out_of_range_rejected():
    reg = ParameterRegistry()
    reg.add(_p("activation_energy", "kJ/mol", Role.INPUT, 999.0, mn=0, mx=500))
    with pytest.raises(ValidationError):
        validate_registry(reg)


def test_nonpositive_temperature_rejected_by_physics():
    reg = ParameterRegistry()
    reg.add(_p("temperature", "degC", Role.INPUT, -300.0))
    with pytest.raises(ValidationError):
        validate_registry(reg)


def test_boolean_is_not_number():
    reg = ParameterRegistry()
    reg.add(_p("temperature", "K", Role.INPUT, True))
    with pytest.raises(ValidationError):
        validate_registry(reg)


def test_user_cannot_set_derived():
    reg = ParameterRegistry()
    reg.add(_p("X", "-", Role.DERIVED, None))
    with pytest.raises(RegistryError):
        reg.set_value("X", 0.5)


def test_unit_conversion_boundary():
    reg = ParameterRegistry()
    reg.add(_p("temperature", "degC", Role.INPUT, 80.0))
    validate_registry(reg)
    assert reg.si("temperature") == pytest.approx(353.15)
