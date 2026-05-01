from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from mhdlc.ir.netlist import Cell, Design, Module, NetBit, Port


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class DesignValidationReport:
    creator: str | None
    modules: dict[str, ValidationReport] = field(default_factory=dict)

    def has_errors(self) -> bool:
        return any(report.errors for report in self.modules.values())

    def to_dict(self) -> dict[str, object]:
        return {
            "creator": self.creator,
            "modules": {
                name: report.to_dict()
                for name, report in self.modules.items()
            },
        }


def _is_constant(bit: NetBit) -> bool:
    return bit in {0, 1, "0", "1"}


def _build_driver_table(module: Module) -> dict[NetBit, list[str]]:
    drivers: dict[NetBit, list[str]] = defaultdict(list)

    for port in module.ports:
        if port.direction == "input":
            for bit in port.bits:
                if not _is_constant(bit):
                    drivers[bit].append(f"port:{port.name}")

    for cell in module.cells:
        for output in cell.output_ports():
            for bit in output.bits:
                if not _is_constant(bit):
                    drivers[bit].append(f"cell:{cell.name}:{output.name}")

    return drivers


def _find_unsupported_cells(module: Module) -> list[str]:
    errors = []
    for cell in module.cells:
        if cell.kind == "UNKNOWN":
            errors.append(f"unsupported cell type '{cell.raw_type}' in cell '{cell.name}'")
    return errors


def _check_single_driver(module: Module, drivers: dict[NetBit, list[str]]) -> list[str]:
    errors = []
    for bit, bit_drivers in drivers.items():
        if len(bit_drivers) > 1:
            errors.append(f"net {bit!r} has multiple drivers: {', '.join(bit_drivers)}")
    for port in module.ports:
        if port.direction == "output":
            for bit in port.bits:
                if _is_constant(bit):
                    continue
                if bit not in drivers:
                    errors.append(f"output port '{port.name}' uses undriven net {bit!r}")
    for cell in module.cells:
        for input_port in cell.input_ports():
            for bit in input_port.bits:
                if _is_constant(bit):
                    continue
                if bit not in drivers:
                    errors.append(
                        f"cell '{cell.name}' input '{input_port.name}' uses undriven net {bit!r}"
                    )
    return errors


def _check_port_widths(cell: Cell) -> list[str]:
    errors = []
    for port in cell.ports:
        expected_width = cell.parameters.get(f"{port.name}_WIDTH")
        if expected_width is None:
            continue
        if int(expected_width) != len(port.bits):
            errors.append(
                f"cell '{cell.name}' port '{port.name}' width mismatch: "
                f"expected {expected_width}, got {len(port.bits)}"
            )
    return errors


def _check_module_shape(module: Module) -> list[str]:
    warnings = []
    hidden_netnames = [
        net.name for net in module.netnames.values() if net.hide_name or net.name.startswith("$")
    ]
    if not module.cells and hidden_netnames:
        warnings.append(
            "module contains no cells but has hidden nets; input may require additional Yosys lowering"
        )
    if module.alias_groups():
        warnings.append(
            f"module contains {len(module.alias_groups())} net alias group(s); alias metadata preserved in IR"
        )
    return warnings


def _cell_dependencies(module: Module) -> tuple[dict[str, set[str]], dict[str, int]]:
    net_to_driver_cell: dict[NetBit, str] = {}
    for cell in module.cells:
        for output in cell.output_ports():
            for bit in output.bits:
                if not _is_constant(bit):
                    net_to_driver_cell[bit] = cell.name

    adjacency: dict[str, set[str]] = {cell.name: set() for cell in module.cells}
    indegree: dict[str, int] = {cell.name: 0 for cell in module.cells}

    for cell in module.cells:
        for input_port in cell.input_ports():
            for bit in input_port.bits:
                if _is_constant(bit):
                    continue
                driver = net_to_driver_cell.get(bit)
                if driver is None:
                    continue
                if cell.name not in adjacency[driver]:
                    adjacency[driver].add(cell.name)
                    indegree[cell.name] += 1

    return adjacency, indegree


def _check_combinational_loops(module: Module) -> list[str]:
    adjacency, indegree = _cell_dependencies(module)
    queue = deque(name for name, degree in indegree.items() if degree == 0)
    visited = 0

    while queue:
        current = queue.popleft()
        visited += 1
        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(module.cells):
        return [
            "combinational loop detected; phase 1 only supports acyclic combinational netlists"
        ]
    return []


def validate_module(module: Module) -> ValidationReport:
    report = ValidationReport()
    report.errors.extend(_find_unsupported_cells(module))
    report.warnings.extend(_check_module_shape(module))

    for cell in module.cells:
        report.errors.extend(_check_port_widths(cell))

    drivers = _build_driver_table(module)
    report.errors.extend(_check_single_driver(module, drivers))

    unsupported_phase1 = [
        cell
        for cell in module.cells
        if cell.kind not in {"AND", "OR", "XOR", "INV", "MUX", "BUF", "UNKNOWN"}
    ]
    for cell in unsupported_phase1:
        report.errors.append(
            f"cell '{cell.name}' of kind '{cell.kind}' is outside the phase-1 combinational subset"
        )

    if not report.errors:
        report.errors.extend(_check_combinational_loops(module))

    if not module.cells:
        report.warnings.append("module contains no cells; net aliases/assigns may need additional lowering")

    return report


def validate_design(design: Design) -> DesignValidationReport:
    return DesignValidationReport(
        creator=design.creator,
        modules={
            module_name: validate_module(module)
            for module_name, module in design.modules.items()
        },
    )
