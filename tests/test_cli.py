import json

from mhdlc.cli import main

from tests.conftest import FIXTURES


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
