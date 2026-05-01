from mhdlc.frontends.yosys_json import load_yosys_module

from tests.conftest import FIXTURES


def test_loads_and_gate_fixture():
    module = load_yosys_module(FIXTURES / "yosys" / "and_gate.json")

    assert module.name == "AND"
    assert len(module.ports) == 4
    assert len(module.cells) == 2
    assert module.cells[0].kind == "AND"
