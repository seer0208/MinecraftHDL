from __future__ import annotations

import argparse
import json
from pathlib import Path

from mhdlc.checks.validation import validate_module
from mhdlc.export.dot import module_to_dot
from mhdlc.frontends.yosys_json import load_yosys_module
from mhdlc.io.json_io import module_to_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mhdlc",
        description="Standalone phase-1 CLI for MinecraftHDL.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser(
        "import", help="Import Yosys JSON and emit normalized MinecraftHDL IR."
    )
    import_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    import_parser.add_argument("--module", help="Module name to import.")
    import_parser.add_argument("--out", type=Path, required=True, help="Output JSON path.")

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a Yosys JSON design through the normalized IR."
    )
    validate_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    validate_parser.add_argument("--module", help="Module name to validate.")

    graph_parser = subparsers.add_parser(
        "graph", help="Export a Graphviz DOT view of the normalized netlist."
    )
    graph_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    graph_parser.add_argument("--module", help="Module name to export.")
    graph_parser.add_argument("--out", type=Path, required=True, help="DOT output path.")

    return parser


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_import(args: argparse.Namespace) -> int:
    module = load_yosys_module(args.input, module_name=args.module)
    report = validate_module(module)
    payload = {
        "format": "mhdlc.netlist.v1",
        "module": module_to_dict(module),
        "validation": report.to_dict(),
    }
    _write_text(args.out, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Imported module '{module.name}' to {args.out}")
    if report.errors:
        print(f"Validation completed with {len(report.errors)} error(s).")
        return 1
    print("Validation completed with no errors.")
    return 0


def run_validate(args: argparse.Namespace) -> int:
    module = load_yosys_module(args.input, module_name=args.module)
    report = validate_module(module)
    print(f"Module: {module.name}")
    print(f"Ports: {len(module.ports)}")
    print(f"Cells: {len(module.cells)}")
    if report.errors:
        print("Errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("Validation passed.")
    return 0


def run_graph(args: argparse.Namespace) -> int:
    module = load_yosys_module(args.input, module_name=args.module)
    dot = module_to_dot(module)
    _write_text(args.out, dot)
    print(f"Wrote graph for module '{module.name}' to {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        return run_import(args)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "graph":
        return run_graph(args)

    parser.error(f"unknown command: {args.command}")
    return 2
