from __future__ import annotations

from mhdlc.ir.netlist import Cell, CellPort, Design, Module, NetName, Port


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


def _netname_to_dict(netname: NetName) -> dict[str, object]:
    return {
        "name": netname.name,
        "bits": list(netname.bits),
        "width": netname.width,
        "hide_name": netname.hide_name,
        "attributes": dict(netname.attributes),
    }


def module_to_dict(module: Module) -> dict[str, object]:
    return {
        "name": module.name,
        "ports": [_port_to_dict(port) for port in module.ports],
        "cells": [_cell_to_dict(cell) for cell in module.cells],
        "netnames": {
            name: _netname_to_dict(netname)
            for name, netname in module.netnames.items()
        },
        "alias_groups": {
            ",".join(str(bit) for bit in bits): list(names)
            for bits, names in module.alias_groups().items()
        },
        "attributes": dict(module.attributes),
    }


def design_to_dict(design: Design) -> dict[str, object]:
    return {
        "creator": design.creator,
        "modules": {
            name: module_to_dict(module)
            for name, module in design.modules.items()
        },
    }
