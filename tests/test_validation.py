from mhdlc.checks.validation import validate_module
from mhdlc.frontends.yosys_json import load_yosys_module

from tests.conftest import FIXTURES


def test_validation_passes_for_simple_and_chain():
    module = load_yosys_module(FIXTURES / "yosys" / "and_gate.json")
    report = validate_module(module)

    assert report.errors == []


def test_validation_detects_combinational_loop():
    module = load_yosys_module(FIXTURES / "yosys" / "bad_loop.json")
    report = validate_module(module)

    assert any("combinational loop detected" in error for error in report.errors)


def test_validation_detects_unsupported_cells():
    module = load_yosys_module(FIXTURES / "yosys" / "unknown_cell.json")
    report = validate_module(module)

    assert any("unsupported cell type" in error for error in report.errors)
