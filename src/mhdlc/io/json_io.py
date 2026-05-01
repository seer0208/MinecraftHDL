from __future__ import annotations

from mhdlc.ir.netlist import Cell, CellPort, Module, Port


def _port_to_dict(port: Port) -> dict[str, object]:
    return {
        "name": port.name,
        "direction": port.direction,
        "width": port.width,
        "bits": list(port.bits),
    }


def _cell_port_to_dict(port: CellPort) -> dict[str, object]:
    return {
        "name": port.name,
        "direction": port.direction,
        "bits": list(port.bits),
    }


def _cell_to_dict(cell: Cell) -> dict[str, object]:
    return {
        "name": cell.name,
        "raw_type": cell.raw_type,
        "kind": cell.kind,
        "ports": [_cell_port_to_dict(port) for port in cell.ports],
        "attributes": dict(cell.attributes),
        "parameters": dict(cell.parameters),
    }


def module_to_dict(module: Module) -> dict[str, object]:
    return {
        "name": module.name,
        "ports": [_port_to_dict(port) for port in module.ports],
        "cells": [_cell_to_dict(cell) for cell in module.cells],
        "netnames": {name: list(bits) for name, bits in module.netnames.items()},
    }
