import pytest

from mhdlc.frontends.yosys_json import load_yosys_design, load_yosys_module
from mhdlc.mapping import MappingError, map_design, map_module
from mhdlc.techlib import load_cell_library

from tests.conftest import FIXTURES, TECHLIB_PATH


def test_map_simple_and_module():
    module = load_yosys_module(FIXTURES / "yosys" / "and_gate.json")
    library = load_cell_library(TECHLIB_PATH)

    mapped = map_module(module, library)

    assert mapped.name == "AND"
    kinds = {instance.kind for instance in mapped.instances}
    assert {"AND", "INPUT", "OUTPUT"} <= kinds
    assert any(net.driver.instance.startswith("cell:") for net in mapped.nets)


def test_map_design_supports_multiple_modules():
    design = load_yosys_design(
        FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "test23.json"
    )
    library = load_cell_library(TECHLIB_PATH)

    mapped = map_design(design, library)

    assert set(mapped.modules) == {"test"}


def test_mapping_fails_for_unknown_logical_kind():
    module = load_yosys_module(FIXTURES / "yosys" / "unknown_cell.json")
    library = load_cell_library(TECHLIB_PATH)

    with pytest.raises(MappingError):
        map_module(module, library)


def test_mapping_fails_when_library_missing_required_cell():
    module = load_yosys_module(FIXTURES / "yosys" / "and_gate.json")
    library = load_cell_library(FIXTURES / "techlib" / "missing_cell.yaml")

    with pytest.raises(MappingError):
        map_module(module, library)


def test_mapping_creates_const1_instance_for_literal_output():
    module = load_yosys_module(FIXTURES / "yosys" / "const_high.json")
    library = load_cell_library(TECHLIB_PATH)

    mapped = map_module(module, library)

    assert any(instance.kind == "CONST1" for instance in mapped.instances)
    assert any(net.constant_value == 1 for net in mapped.nets)
