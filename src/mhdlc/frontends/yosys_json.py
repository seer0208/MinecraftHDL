from __future__ import annotations

import json
from pathlib import Path

from mhdlc.ir.netlist import Cell, CellPort, Design, Module, NetName, Port


SUPPORTED_CELL_TYPES: dict[str, str] = {
    "$and": "AND",
    "$_AND_": "AND",
    "$or": "OR",
    "$_OR_": "OR",
    "OR": "OR",
    "$xor": "XOR",
    "$_XOR_": "XOR",
    "$not": "INV",
    "$_NOT_": "INV",
    "$mux": "MUX",
    "$_MUX_": "MUX",
    "$_BUF_": "BUF",
    "$buf": "BUF",
}

SEQUENTIAL_CELL_TYPES: dict[str, str] = {
    "$dff": "DFF",
    "$_DFF_P_": "DFF",
    "$_DFF_N_": "DFF",
    "$adff": "DFF",
    "$dlatch": "DLATCH",
    "$dlatch_p": "DLATCH",
    "$_DLATCH_P_": "DLATCH",
    "$_DLATCH_N_": "DLATCH",
}


def _normalize_bits(bits: list[int | str]) -> tuple[int | str, ...]:
    normalized: list[int | str] = []
    for bit in bits:
        if isinstance(bit, int):
            normalized.append(bit)
        elif isinstance(bit, str):
            normalized.append(bit)
        else:
            raise TypeError(f"unsupported bit value: {bit!r}")
    return tuple(normalized)


def _normalize_kind(raw_type: str) -> str:
    if raw_type in SEQUENTIAL_CELL_TYPES:
        return SEQUENTIAL_CELL_TYPES[raw_type]
    return SUPPORTED_CELL_TYPES.get(raw_type, "UNKNOWN")


def list_yosys_modules(path: Path) -> list[str]:
    return list(load_yosys_design(path).modules.keys())

def _module_from_data(module_name: str, module_data: dict[str, object]) -> Module:
    ports = []
    for port_name, port_data in module_data.get("ports", {}).items():
        ports.append(
            Port(
                name=port_name,
                direction=port_data["direction"],
                bits=_normalize_bits(port_data.get("bits", [])),
            )
        )

    cells = []
    for cell_name, cell_data in module_data.get("cells", {}).items():
        cell_ports = []
        directions = cell_data.get("port_directions", {})
        connections = cell_data.get("connections", {})
        for conn_name, conn_bits in connections.items():
            cell_ports.append(
                CellPort(
                    name=conn_name,
                    direction=directions[conn_name],
                    bits=_normalize_bits(conn_bits),
                )
            )
        cells.append(
            Cell(
                name=cell_name,
                raw_type=cell_data["type"],
                kind=_normalize_kind(cell_data["type"]),
                ports=tuple(cell_ports),
                attributes=dict(cell_data.get("attributes", {})),
                parameters=dict(cell_data.get("parameters", {})),
            )
        )

    netnames = {}
    for name, net_data in module_data.get("netnames", {}).items():
        netnames[name] = NetName(
            name=name,
            bits=_normalize_bits(net_data.get("bits", [])),
            hide_name=bool(net_data.get("hide_name", 0)),
            attributes=dict(net_data.get("attributes", {})),
        )

    return Module(
        name=module_name,
        ports=tuple(ports),
        cells=tuple(cells),
        netnames=netnames,
        attributes=dict(module_data.get("attributes", {})),
    )


def load_yosys_design(path: Path) -> Design:
    payload = json.loads(path.read_text(encoding="utf-8"))
    modules: dict[str, object] = payload.get("modules", {})
    if not modules:
        raise ValueError(f"no modules found in {path}")

    return Design(
        creator=payload.get("creator"),
        modules={name: _module_from_data(name, data) for name, data in modules.items()},
    )


def load_yosys_module(path: Path, module_name: str | None = None) -> Module:
    design = load_yosys_design(path)
    modules = design.modules

    if module_name is None:
        selected_name = next(iter(modules))
    else:
        selected_name = module_name
        if selected_name not in modules:
            available = ", ".join(modules.keys())
            raise ValueError(f"module '{selected_name}' not found; available modules: {available}")

    return modules[selected_name]
