from __future__ import annotations

from mhdlc.ir.netlist import Cell, CellPort, Design, Module, NetName, Port
from mhdlc.ir.redstone import (
    RedstoneCellInstance,
    RedstoneDesign,
    RedstoneModule,
    RedstoneNet,
    RedstonePinRef,
)


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


def _redstone_pin_ref_to_dict(pin_ref: RedstonePinRef) -> dict[str, str]:
    return {
        "instance": pin_ref.instance,
        "pin": pin_ref.pin,
    }


def _redstone_instance_to_dict(instance: RedstoneCellInstance) -> dict[str, object]:
    return {
        "name": instance.name,
        "library_cell": instance.library_cell,
        "kind": instance.kind,
        "source_logical_module": instance.source_logical_module,
        "source_logical_cell": instance.source_logical_cell,
        "source_port": instance.source_port,
        "size": list(instance.size),
        "delay_ticks": instance.delay_ticks,
        "max_wire_without_repeater": instance.max_wire_without_repeater,
    }


def _redstone_net_to_dict(net: RedstoneNet) -> dict[str, object]:
    return {
        "name": net.name,
        "logical_bit": net.logical_bit,
        "aliases": list(net.aliases),
        "driver": _redstone_pin_ref_to_dict(net.driver),
        "sinks": [_redstone_pin_ref_to_dict(pin_ref) for pin_ref in net.sinks],
        "constant_value": net.constant_value,
    }


def redstone_module_to_dict(module: RedstoneModule) -> dict[str, object]:
    return {
        "name": module.name,
        "source_logical_module": module.source_logical_module,
        "instances": [_redstone_instance_to_dict(instance) for instance in module.instances],
        "nets": [_redstone_net_to_dict(net) for net in module.nets],
    }


def redstone_design_to_dict(design: RedstoneDesign) -> dict[str, object]:
    return {
        "library_name": design.library_name,
        "library_version": design.library_version,
        "source_creator": design.source_creator,
        "modules": {
            module_name: redstone_module_to_dict(module)
            for module_name, module in design.modules.items()
        },
    }
