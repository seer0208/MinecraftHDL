from mhdlc.frontends.yosys_json import list_yosys_modules, load_yosys_design, load_yosys_module

from tests.conftest import FIXTURES


def test_loads_and_gate_fixture():
    module = load_yosys_module(FIXTURES / "yosys" / "and_gate.json")

    assert module.name == "AND"
    assert len(module.ports) == 4
    assert len(module.cells) == 2
    assert module.cells[0].kind == "AND"


def test_lists_modules_in_legacy_fixture():
    modules = list_yosys_modules(FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "and.json")

    assert modules == ["AND", "counter"]


def test_loads_full_design_and_preserves_creator():
    design = load_yosys_design(FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "and.json")

    assert design.creator is not None
    assert set(design.modules) == {"AND", "counter"}
    assert design.modules["AND"].netnames["a"].bits == (2,)
