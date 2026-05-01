import json

from mhdlc.cli import main

from tests.conftest import FIXTURES, TECHLIB_PATH


def test_import_command_writes_normalized_json(tmp_path):
    out_path = tmp_path / "and_gate.mhdl.json"

    rc = main(
        [
            "import",
            str(FIXTURES / "yosys" / "and_gate.json"),
            "--out",
            str(out_path),
        ]
    )

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["format"] == "mhdlc.netlist.v1"
    assert payload["module"]["name"] == "AND"


def test_validate_command_fails_for_unsupported_cell():
    rc = main(["validate", str(FIXTURES / "yosys" / "unknown_cell.json")])
    assert rc == 1


def test_modules_command_lists_names(capsys):
    rc = main(["modules", str(FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "and.json")])

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["AND", "counter"]


def test_validate_all_modules_json_output(capsys):
    rc = main(
        [
            "validate",
            str(FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "and.json"),
            "--all-modules",
            "--json",
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert set(payload["modules"]) == {"AND", "counter"}


def test_import_all_modules_writes_design_json(tmp_path):
    out_path = tmp_path / "legacy_and.design.json"

    rc = main(
        [
            "import",
            str(FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "and.json"),
            "--all-modules",
            "--out",
            str(out_path),
        ]
    )

    assert rc == 1
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["format"] == "mhdlc.design.v1"
    assert set(payload["design"]["modules"]) == {"AND", "counter"}


def test_techlib_check_command(capsys):
    rc = main(["techlib", "check", str(TECHLIB_PATH)])

    assert rc == 0
    captured = capsys.readouterr()
    assert "Library: redstone_v1" in captured.out


def test_techlib_check_command_fails_for_invalid_library(capsys):
    rc = main(["techlib", "check", str(FIXTURES / "techlib" / "invalid_orientation.yaml")])

    assert rc == 1
    captured = capsys.readouterr()
    assert "Technology library error:" in captured.out


def test_map_command_writes_redstone_netlist(tmp_path):
    out_path = tmp_path / "and_gate.redstone.json"

    rc = main(
        [
            "map",
            str(FIXTURES / "yosys" / "and_gate.json"),
            "--lib",
            str(TECHLIB_PATH),
            "--out",
            str(out_path),
        ]
    )

    assert rc == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["format"] == "mhdlc.redstone.v1"
    assert payload["module"]["name"] == "AND"
    assert any(instance["kind"] == "AND" for instance in payload["module"]["instances"])


def test_map_command_fails_for_sequential_fixture(capsys, tmp_path):
    out_path = tmp_path / "counter.redstone.json"

    rc = main(
        [
            "map",
            str(FIXTURES.parent.parent / "src" / "main" / "tests" / "json files" / "counter.json"),
            "--module",
            "counter",
            "--lib",
            str(TECHLIB_PATH),
            "--out",
            str(out_path),
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["errors"]
