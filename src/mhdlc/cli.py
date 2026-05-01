from __future__ import annotations

import argparse
import json
from pathlib import Path

from mhdlc.checks.validation import validate_design, validate_module
from mhdlc.export.dot import module_to_dot
from mhdlc.frontends.yosys_json import list_yosys_modules, load_yosys_design, load_yosys_module
from mhdlc.io.json_io import (
    design_to_dict,
    module_to_dict,
    redstone_design_to_dict,
    redstone_module_to_dict,
)
from mhdlc.mapping import MappingError, map_design, map_module
from mhdlc.techlib import CellLibraryError, load_cell_library


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mhdlc",
        description="Standalone compiler CLI for MinecraftHDL.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    techlib_parser = subparsers.add_parser(
        "techlib", help="Redstone technology library operations."
    )
    techlib_subparsers = techlib_parser.add_subparsers(dest="techlib_command", required=True)
    techlib_check_parser = techlib_subparsers.add_parser(
        "check", help="Validate a redstone technology library YAML file."
    )
    techlib_check_parser.add_argument("library", type=Path, help="Path to a YAML tech library.")

    modules_parser = subparsers.add_parser(
        "modules", help="List modules available in a Yosys JSON design."
    )
    modules_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")

    import_parser = subparsers.add_parser(
        "import", help="Import Yosys JSON and emit normalized MinecraftHDL IR."
    )
    import_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    import_parser.add_argument("--module", help="Module name to import.")
    import_parser.add_argument(
        "--all-modules",
        action="store_true",
        help="Import every module in the Yosys JSON file.",
    )
    import_parser.add_argument("--out", type=Path, required=True, help="Output JSON path.")

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a Yosys JSON design through the normalized IR."
    )
    validate_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    validate_parser.add_argument("--module", help="Module name to validate.")
    validate_parser.add_argument(
        "--all-modules",
        action="store_true",
        help="Validate every module in the Yosys JSON file.",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the validation report as JSON.",
    )

    graph_parser = subparsers.add_parser(
        "graph", help="Export a Graphviz DOT view of the normalized netlist."
    )
    graph_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    graph_parser.add_argument("--module", help="Module name to export.")
    graph_parser.add_argument("--out", type=Path, required=True, help="DOT output path.")

    map_parser = subparsers.add_parser(
        "map", help="Map logical netlists to the redstone technology netlist."
    )
    map_parser.add_argument("input", type=Path, help="Path to a Yosys JSON file.")
    map_parser.add_argument("--module", help="Module name to map.")
    map_parser.add_argument(
        "--all-modules",
        action="store_true",
        help="Map every module in the Yosys JSON file.",
    )
    map_parser.add_argument("--lib", type=Path, required=True, help="Path to the YAML tech library.")
    map_parser.add_argument("--out", type=Path, required=True, help="Mapped JSON output path.")

    return parser


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_modules(args: argparse.Namespace) -> int:
    module_names = list_yosys_modules(args.input)
    for module_name in module_names:
        print(module_name)
    return 0


def run_techlib_check(args: argparse.Namespace) -> int:
    try:
        library = load_cell_library(args.library)
    except CellLibraryError as exc:
        print(f"Technology library error: {exc}")
        return 1

    print(f"Library: {library.name}")
    print(f"Version: {library.version}")
    print(f"Cells: {len(library.cells)}")
    print(f"Kinds: {', '.join(library.kinds())}")
    return 0


def run_import(args: argparse.Namespace) -> int:
    if args.module and args.all_modules:
        raise ValueError("--module and --all-modules are mutually exclusive")

    if args.all_modules:
        design = load_yosys_design(args.input)
        report = validate_design(design)
        payload = {
            "format": "mhdlc.design.v1",
            "design": design_to_dict(design),
            "validation": report.to_dict(),
        }
        _write_text(args.out, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"Imported design with {len(design.modules)} module(s) to {args.out}")
        if report.has_errors():
            error_count = sum(len(module_report.errors) for module_report in report.modules.values())
            print(f"Validation completed with {error_count} error(s).")
            return 1
        print("Validation completed with no errors.")
        return 0

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
    if args.module and args.all_modules:
        raise ValueError("--module and --all-modules are mutually exclusive")

    if args.all_modules:
        design = load_yosys_design(args.input)
        report = validate_design(design)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
            return 1 if report.has_errors() else 0
        print(f"Design creator: {design.creator or 'unknown'}")
        print(f"Modules: {len(design.modules)}")
        for module_name, module_report in report.modules.items():
            status = "ERROR" if module_report.errors else "OK"
            print(f"{module_name}: {status}")
            for error in module_report.errors:
                print(f"  - {error}")
        return 1 if report.has_errors() else 0

    module = load_yosys_module(args.input, module_name=args.module)
    report = validate_module(module)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 1 if report.errors else 0
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


def run_map(args: argparse.Namespace) -> int:
    if args.module and args.all_modules:
        raise ValueError("--module and --all-modules are mutually exclusive")

    try:
        library = load_cell_library(args.lib)
    except CellLibraryError as exc:
        print(f"Technology library error: {exc}")
        return 1

    if args.all_modules:
        design = load_yosys_design(args.input)
        validation = validate_design(design)
        if validation.has_errors():
            print(json.dumps(validation.to_dict(), indent=2, sort_keys=True))
            return 1
        mapped_design = map_design(design, library)
        payload = {
            "format": "mhdlc.redstone.v1",
            "design": redstone_design_to_dict(mapped_design),
        }
        _write_text(args.out, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"Mapped design with {len(mapped_design.modules)} module(s) to {args.out}")
        return 0

    module = load_yosys_module(args.input, module_name=args.module)
    validation = validate_module(module)
    if validation.errors:
        print(json.dumps(validation.to_dict(), indent=2, sort_keys=True))
        return 1

    try:
        mapped_module = map_module(module, library)
    except MappingError as exc:
        print(f"Mapping error: {exc}")
        return 1

    payload = {
        "format": "mhdlc.redstone.v1",
        "module": redstone_module_to_dict(mapped_module),
        "library": {
            "name": library.name,
            "version": library.version,
        },
    }
    _write_text(args.out, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Mapped module '{module.name}' to {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "techlib":
        if args.techlib_command == "check":
            return run_techlib_check(args)
        parser.error(f"unknown techlib command: {args.techlib_command}")
    if args.command == "modules":
        return run_modules(args)
    if args.command == "import":
        return run_import(args)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "graph":
        return run_graph(args)
    if args.command == "map":
        return run_map(args)

    parser.error(f"unknown command: {args.command}")
    return 2
