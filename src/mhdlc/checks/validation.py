from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from mhdlc.ir.netlist import Cell, Module, NetBit, Port


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "errors": list(self.errors),
            "warnings": list(self.warnings),
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
                if driver is None or driver == cell.name:
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

    drivers = _build_driver_table(module)
    report.errors.extend(_check_single_driver(module, drivers))

    unsupported_sequential = [cell for cell in module.cells if cell.kind not in {"AND", "OR", "XOR", "INV", "MUX", "UNKNOWN"}]
    for cell in unsupported_sequential:
        report.errors.append(
            f"cell '{cell.name}' of kind '{cell.kind}' is outside the phase-1 combinational subset"
        )

    if not report.errors:
        report.errors.extend(_check_combinational_loops(module))

    if not module.cells:
        report.warnings.append("module contains no cells; net aliases/assigns may need additional lowering")

    return report
